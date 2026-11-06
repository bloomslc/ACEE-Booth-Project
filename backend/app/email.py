import os
from dataclasses import dataclass

import httpx


class EmailDeliveryError(RuntimeError):
	"""Raised when Resend cannot accept an email delivery request."""


@dataclass(frozen=True)
class EmailDelivery:
	recipient: str
	guest_name: str
	image_url: str | None = None
	session_id: str | None = None


def send_photo_email(delivery: EmailDelivery) -> str:
	api_key = os.getenv("RESEND_API_KEY")
	sender = os.getenv("RESEND_FROM_EMAIL")
	if not api_key or not sender:
		raise EmailDeliveryError(
			"RESEND_API_KEY and RESEND_FROM_EMAIL must be configured"
		)

	payload: dict[str, object] = {"from": sender, "to": [delivery.recipient]}
	template_id = os.getenv("RESEND_TEMPLATE_ID")
	image_variable = os.getenv("RESEND_TEMPLATE_IMAGE_VARIABLE", "PHOTO_IMAGE")

	if template_id:
		if not delivery.image_url:
			raise EmailDeliveryError("A bucket image URL is required for the email template")
		if not delivery.session_id:
			raise EmailDeliveryError("A session ID is required for the email template")
		variables: dict[str, str] = {
			"GUEST_NAME": delivery.guest_name or "there",
			image_variable: delivery.image_url,
			"SESSION_ID": delivery.session_id,
		}
		payload["template"] = {"id": template_id, "variables": variables}
	else:
		payload.update(
			{
				"subject": "Your portrait booth photo",
				"html": (
					f"<p>Hi {delivery.guest_name or 'there'},</p>"
					"<p>Thanks for visiting the portrait booth. Your photo is attached.</p>"
				),
			}
		)

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

