import os
import logging
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field
from dotenv import load_dotenv

from .camera import CameraCaptureError, bypass_image_path, capture_photo, capture_preview_frame, is_dev_bypass, photo_storage_dir, preview_stream
from .database import DatabaseError, create_session, initialize, is_configured, record_delivery, record_photo
from .email import EmailDelivery, EmailDeliveryError, send_photo_email
from .storage import ImageStorageError, upload_image

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


app = FastAPI(title="ACEE Portrait Booth API")
app.add_middleware(
	CORSMiddleware,
	allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")],
	allow_methods=["POST", "GET"],
	allow_headers=["Content-Type"],
)
photo_storage_dir().mkdir(parents=True, exist_ok=True)
app.mount("/images", StaticFiles(directory=photo_storage_dir()), name="images")


@app.on_event("startup")
def startup() -> None:
	if is_configured():
		initialize()


@app.get("/api/v1/health")
def health() -> dict[str, str]:
	return {
		"status": "ok",
		"email_provider": "resend",
		"database": "neon" if is_configured() else "disabled",
		"dev_bypass": "enabled" if is_dev_bypass() else "disabled",
		"image_storage": "s3" if os.getenv("S3_BUCKET") and not is_dev_bypass() else "local",
	}


@app.get("/api/v1/dev-bypass-image")
def dev_bypass_image() -> FileResponse:
	if not is_dev_bypass():
		raise HTTPException(status_code=404, detail="Development bypass is disabled")
	return FileResponse(bypass_image_path(), media_type="image/jpeg")


@app.post("/api/v1/capture", response_model=CaptureResponse)
def capture(request: Request) -> CaptureResponse:
	try:
		captured_photo = capture_photo()
	except CameraCaptureError as error:
		raise HTTPException(status_code=503, detail=str(error)) from error
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
			raise HTTPException(status_code=503, detail=str(error)) from error

	image_url = remote_url
	if captured_photo.local_path and not image_url:
		filename = Path(captured_photo.local_path).name
		configured_base_url = os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/")
		public_base_url = configured_base_url or str(request.base_url).rstrip("/")
		if "0.0.0.0" in public_base_url:
			public_base_url = str(request.base_url).rstrip("/")
		image_url = f"{public_base_url.rstrip('/')}/images/{filename}"
	if not image_url:
		image_url = f"{str(request.base_url).rstrip('/')}/api/v1/dev-bypass-image"

	return CaptureResponse(
		status="captured",
		image_url=image_url,
		session_id=session_id,
		local_path=captured_photo.local_path,
		remote_url=remote_url,
	)


@app.get("/api/v1/camera/preview")
def preview() -> StreamingResponse:
	try:
		first_frame = capture_preview_frame()
	except CameraCaptureError as error:
		raise HTTPException(status_code=503, detail=str(error)) from error

	return StreamingResponse(
		preview_stream(first_frame),
		media_type="multipart/x-mixed-replace; boundary=frame",
		headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
	)


@app.post("/api/v1/deliveries/email", response_model=EmailDeliveryResponse)
def deliver_email(request: EmailDeliveryRequest) -> EmailDeliveryResponse:
	logger.info(
		"Email delivery requested recipient=%s session_id=%s image_url_present=%s dev_bypass=%s",
		request.email,
		request.session_id,
		bool(request.image_url),
		is_dev_bypass(),
	)
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
