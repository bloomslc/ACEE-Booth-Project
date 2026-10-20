import base64
import binascii
import os
from dataclasses import dataclass

import httpx


class EmailDeliveryError(RuntimeError):
	"""Raised when Resend cannot accept an email delivery request."""


@dataclass(frozen=True)
class EmailDelivery:
	recipient: str
	guest_name: str
	image_data_url: str | None = None


def send_photo_email(delivery: EmailDelivery) -> str:
	api_key = os.getenv("RESEND_API_KEY")
	sender = os.getenv("RESEND_FROM_EMAIL")
	if not api_key or not sender:
		raise EmailDeliveryError(
			"RESEND_API_KEY and RESEND_FROM_EMAIL must be configured"
		)

	payload: dict[str, object] = {
		"from": sender,
		"to": [delivery.recipient],
		"subject": "Your portrait booth photo",
		"html": (
			f"<p>Hi {delivery.guest_name or 'there'},</p>"
			"<p>Thanks for visiting the portrait booth. Your photo is attached.</p>"
		),
	}

	if delivery.image_data_url:
		encoded_image = _data_url_to_base64(delivery.image_data_url)
		payload["attachments"] = [
			{"filename": "portrait-booth-photo.jpg", "content": encoded_image}
		]

	try:
		response = httpx.post(
			"https://api.resend.com/emails",
			headers={"Authorization": f"Bearer {api_key}"},
			json=payload,
			timeout=20,
		)
		response.raise_for_status()
	except (httpx.HTTPError, ValueError) as error:
		raise EmailDeliveryError("Resend rejected the email") from error

	return str(response.json().get("id", ""))


def _data_url_to_base64(data_url: str) -> str:
	try:
		header, encoded = data_url.split(",", 1)
		if not header.startswith("data:image/") or ";base64" not in header:
			raise ValueError
		base64.b64decode(encoded, validate=True)
		return encoded
	except (ValueError, binascii.Error) as error:
		raise EmailDeliveryError("The photo must be a base64 image data URL") from error
