import logging
import os
from dataclasses import dataclass
from email.utils import parseaddr

import httpx

logger = logging.getLogger(__name__)


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
	_, sender_address = parseaddr(sender)
	if "@" not in sender_address:
		raise EmailDeliveryError(
			"RESEND_FROM_EMAIL must be a verified address, for example "
			'"Portrait Booth <booth@example.com>"'
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
					"<p>Thanks for visiting the portrait booth.</p>"
				),
			}
		)

	try:
		logger.info(
			"Sending email through Resend recipient=%s template=%s image_url_present=%s",
			delivery.recipient,
			bool(template_id),
			bool(delivery.image_url),
		)
		response = httpx.post(
			"https://api.resend.com/emails",
			headers={"Authorization": f"Bearer {api_key}"},
			json=payload,
			timeout=20,
		)
		response.raise_for_status()
		logger.info(
			"Resend accepted email recipient=%s provider_id=%s",
			delivery.recipient,
			response.json().get("id", ""),
		)
	except httpx.HTTPStatusError as error:
		detail = error.response.text[:500]
		raise EmailDeliveryError(f"Resend rejected the email: {detail}") from error
	except (httpx.HTTPError, ValueError) as error:
		raise EmailDeliveryError("Resend rejected the email") from error

	return str(response.json().get("id", ""))

