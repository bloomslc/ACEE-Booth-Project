import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field

from .auth import require_token
from .camera import (
	CameraCaptureError,
	CapturedPhoto,
	bypass_image_path,
	capture_photo,
	ingest_uploaded_photo,
	photo_storage_dir,
	preview_stream,
)
from .config import camera_mode, is_dev_bypass, is_ftp_mode
from .database import DatabaseError, create_session, initialize, is_configured, record_delivery, record_photo
from .email import EmailDelivery, EmailDeliveryError, send_photo_email
from .ftp import INBOX, RECEIVER, FtpConfigurationError, Upload, start_from_environment
from .storage import ImageStorageError, delete_image, object_key, public_base_url, upload_image
from .storage import is_configured as is_storage_configured

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

logger = logging.getLogger(__name__)


class EmailDeliveryRequest(BaseModel):
	name: str = Field(default="Guest", max_length=120)
	email: EmailStr
	image_url: str | None = None
	session_id: str | None = None


class EmailDeliveryResponse(BaseModel):
	status: str
	provider_id: str


class CaptureResponse(BaseModel):
	status: str
	image_url: str
	session_id: str
	local_path: str | None
	remote_url: str | None


def allowed_origins() -> list[str]:
	"""Allow any origin unless FRONTEND_ORIGIN lists specific ones; the booth token is the access control."""
	origins = [origin.strip() for origin in os.getenv("FRONTEND_ORIGIN", "").split(",") if origin.strip()]
	return origins or ["*"]


def build_public_url(request: Request, path: str) -> str:
	"""Build a URL on the host the client used to reach this API, so it works for any server address."""
	return f"{str(request.base_url).rstrip('/')}/{path.lstrip('/')}"


def is_allowed_image_url(image_url: str, request: Request) -> bool:
	"""Only accept image URLs that point at this booth's API or image bucket."""
	prefixes = [
		build_public_url(request, "/images/"),
		build_public_url(request, "/api/v1/dev-bypass-image"),
	]
	if is_storage_configured():
		prefixes.append(f"{public_base_url()}/")
	return image_url.startswith(tuple(prefixes))


@asynccontextmanager
async def lifespan(_: FastAPI):
	if is_configured():
		initialize()
	if is_ftp_mode():
		try:
			start_from_environment()
		except (FtpConfigurationError, OSError) as error:
			raise RuntimeError(f"The camera FTP server could not start: {error}") from error
	yield
	RECEIVER.stop()


app = FastAPI(title="ACEE Portrait Booth API", lifespan=lifespan)
app.add_middleware(
	CORSMiddleware,
	allow_origins=allowed_origins(),
	allow_methods=["POST", "GET"],
	allow_headers=["Content-Type", "X-Booth-Token"],
)
photo_storage_dir().mkdir(parents=True, exist_ok=True)
app.mount("/images", StaticFiles(directory=photo_storage_dir()), name="images")


@app.get("/api/v1/health")
def health() -> dict[str, str]:
	return {
		"status": "ok",
		"email_provider": "resend",
		"database": "neon" if is_configured() else "disabled",
		"dev_bypass": "enabled" if is_dev_bypass() else "disabled",
		"camera_mode": camera_mode(),
		"image_storage": "s3" if os.getenv("S3_BUCKET") and not is_dev_bypass() else "local",
	}


@app.get("/api/v1/dev-bypass-image")
def dev_bypass_image() -> FileResponse:
	if not is_dev_bypass():
		raise HTTPException(status_code=404, detail="Development bypass is disabled")
	return FileResponse(bypass_image_path(), media_type="image/jpeg")


async def wait_for_camera_upload(request: Request) -> Upload:
	"""Wait for the next photo the camera uploads over FTP, giving up if the client leaves or time runs out."""
	timeout = float(os.getenv("FTP_CAPTURE_TIMEOUT", "120"))
	baseline = INBOX.latest_sequence()
	loop = asyncio.get_running_loop()
	deadline = loop.time() + timeout
	while loop.time() < deadline:
		upload = INBOX.claim_after(baseline)
		if upload:
			return upload
		if await request.is_disconnected():
			raise HTTPException(status_code=499, detail="The client stopped waiting for a photo")
		await asyncio.sleep(0.25)
	raise HTTPException(status_code=408, detail="No photo arrived from the camera yet")


@app.post("/api/v1/capture", response_model=CaptureResponse, dependencies=[Depends(require_token)])
async def capture(request: Request) -> CaptureResponse:
	try:
		if is_ftp_mode():
			upload = await wait_for_camera_upload(request)
			captured_photo = await run_in_threadpool(ingest_uploaded_photo, upload.path)
		else:
			captured_photo = await run_in_threadpool(capture_photo)
	except CameraCaptureError as error:
		raise HTTPException(status_code=503, detail=str(error)) from error
	return await run_in_threadpool(publish_capture, request, captured_photo)


def publish_capture(request: Request, captured_photo: CapturedPhoto) -> CaptureResponse:
	logger.info(
		"Capture completed local_path_present=%s dev_bypass=%s s3_configured=%s database_configured=%s",
		bool(captured_photo.local_path),
		is_dev_bypass(),
		bool(os.getenv("S3_BUCKET")),
		is_configured(),
	)

	session_id = str(uuid4())
	remote_url = None
	if captured_photo.local_path and not is_dev_bypass() and os.getenv("S3_BUCKET"):
		try:
			remote_url = upload_image(captured_photo.local_path, session_id)
			logger.info("Capture uploaded to image storage session_id=%s", session_id)
		except ImageStorageError as error:
			logger.exception("Capture upload failed session_id=%s", session_id)
			raise HTTPException(status_code=502, detail=str(error)) from error

	if is_configured() and captured_photo.local_path:
		try:
			create_session(session_id)
			record_photo(session_id, captured_photo.local_path, remote_url)
			logger.info("Capture recorded in database session_id=%s", session_id)
		except DatabaseError as error:
			logger.exception("Capture database record failed session_id=%s", session_id)
			if remote_url:
				delete_image(object_key(captured_photo.local_path, session_id))
			Path(captured_photo.local_path).unlink(missing_ok=True)
			raise HTTPException(status_code=503, detail=str(error)) from error

	image_url = remote_url
	if captured_photo.local_path and not image_url:
		image_url = build_public_url(request, f"/images/{Path(captured_photo.local_path).name}")
	if not image_url:
		image_url = build_public_url(request, "/api/v1/dev-bypass-image")

	return CaptureResponse(
		status="captured",
		image_url=image_url,
		session_id=session_id,
		local_path=captured_photo.local_path,
		remote_url=remote_url,
	)


@app.get("/api/v1/camera/preview", dependencies=[Depends(require_token)])
def preview() -> StreamingResponse:
	if is_ftp_mode():
		raise HTTPException(status_code=404, detail="Live preview is not available in FTP mode")
	try:
		frames = preview_stream()
	except CameraCaptureError as error:
		raise HTTPException(status_code=503, detail=str(error)) from error

	return StreamingResponse(
		frames,
		media_type="multipart/x-mixed-replace; boundary=frame",
		headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
	)


@app.post("/api/v1/deliveries/email", response_model=EmailDeliveryResponse, dependencies=[Depends(require_token)])
def deliver_email(request: EmailDeliveryRequest, http_request: Request) -> EmailDeliveryResponse:
	logger.info(
		"Email delivery requested recipient=%s session_id=%s image_url_present=%s dev_bypass=%s",
		request.email,
		request.session_id,
		bool(request.image_url),
		is_dev_bypass(),
	)
	if request.image_url and not is_dev_bypass() and not is_allowed_image_url(request.image_url, http_request):
		raise HTTPException(status_code=400, detail="The image URL does not belong to this booth")
	if is_dev_bypass():
		logger.warning("Email delivery skipped because DEV_BYPASS is enabled")
		provider_id = "dev-bypass"
		status = "skipped"
	else:
		try:
			provider_id = send_photo_email(
				EmailDelivery(
					recipient=str(request.email),
					guest_name=request.name.strip(),
					image_url=request.image_url,
					session_id=request.session_id,
				)
			)
		except EmailDeliveryError as error:
			raise HTTPException(status_code=502, detail=str(error)) from error
		status = "sent"

	if is_configured():
		try:
			record_delivery(request.session_id, str(request.email), provider_id, status)
		except DatabaseError as error:
			raise HTTPException(status_code=503, detail=str(error)) from error

	return EmailDeliveryResponse(status=status, provider_id=provider_id)
