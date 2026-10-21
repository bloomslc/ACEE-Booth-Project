import os
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from dotenv import load_dotenv

from .camera import CameraCaptureError, capture_photo, capture_preview, is_dev_bypass
from .database import DatabaseError, create_session, initialize, is_configured, record_delivery, record_photo
from .email import EmailDelivery, EmailDeliveryError, send_photo_email

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


class EmailDeliveryRequest(BaseModel):
	name: str = Field(default="Guest", max_length=120)
	email: EmailStr
	image_data_url: str | None = None
	session_id: str | None = None


class EmailDeliveryResponse(BaseModel):
	status: str
	provider_id: str


class CaptureResponse(BaseModel):
	status: str
	image_data_url: str
	session_id: str


class PreviewResponse(BaseModel):
	status: str
	image_data_url: str


app = FastAPI(title="ACEE Portrait Booth API")
app.add_middleware(
	CORSMiddleware,
	allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")],
	allow_methods=["POST", "GET"],
	allow_headers=["Content-Type"],
)


@app.on_event("startup")
def startup() -> None:
	if is_configured():
		initialize()


@app.get("/api/v1/health")
def health() -> dict[str, str]:
	return {"status": "ok", "email_provider": "resend", "database": "mysql" if is_configured() else "disabled"}


@app.post("/api/v1/capture", response_model=CaptureResponse)
def capture() -> CaptureResponse:
	try:
		image_data_url = capture_photo()
	except CameraCaptureError as error:
		raise HTTPException(status_code=503, detail=str(error)) from error

	session_id = str(uuid4())
	if is_configured():
		try:
			create_session(session_id)
			record_photo(session_id, image_data_url)
		except DatabaseError as error:
			raise HTTPException(status_code=503, detail=str(error)) from error

	return CaptureResponse(status="captured", image_data_url=image_data_url, session_id=session_id)


@app.post("/api/v1/camera/preview", response_model=PreviewResponse)
def preview() -> PreviewResponse:
	try:
		image_data_url = capture_preview()
	except CameraCaptureError as error:
		raise HTTPException(status_code=503, detail=str(error)) from error

	return PreviewResponse(status="preview", image_data_url=image_data_url)


@app.post("/api/v1/deliveries/email", response_model=EmailDeliveryResponse)
def deliver_email(request: EmailDeliveryRequest) -> EmailDeliveryResponse:
	if is_dev_bypass():
		provider_id = "dev-bypass"
		status = "skipped"
	else:
		try:
			provider_id = send_photo_email(
				EmailDelivery(
					recipient=str(request.email),
					guest_name=request.name.strip(),
					image_data_url=request.image_data_url,
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
