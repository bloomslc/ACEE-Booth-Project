import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

from .email import EmailDelivery, EmailDeliveryError, send_photo_email


class EmailDeliveryRequest(BaseModel):
	name: str = Field(default="Guest", max_length=120)
	email: EmailStr
	image_data_url: str | None = None


class EmailDeliveryResponse(BaseModel):
	status: str
	provider_id: str


app = FastAPI(title="ACEE Portrait Booth API")
app.add_middleware(
	CORSMiddleware,
	allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")],
	allow_methods=["POST", "GET"],
	allow_headers=["Content-Type"],
)


@app.get("/api/v1/health")
def health() -> dict[str, str]:
	return {"status": "ok", "email_provider": "resend"}


@app.post("/api/v1/deliveries/email", response_model=EmailDeliveryResponse)
def deliver_email(request: EmailDeliveryRequest) -> EmailDeliveryResponse:
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

	return EmailDeliveryResponse(status="sent", provider_id=provider_id)
