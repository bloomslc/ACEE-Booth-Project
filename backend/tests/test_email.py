import httpx
import pytest

from app import email
from app.email import EmailDelivery, EmailDeliveryError, send_photo_email


class FakeResponse:
	def raise_for_status(self) -> None:
		return None

	def json(self) -> dict[str, str]:
		return {"id": "email-123"}


@pytest.fixture
def sent_payloads(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
	monkeypatch.setenv("RESEND_API_KEY", "re_test")
	monkeypatch.setenv("RESEND_FROM_EMAIL", "Booth <booth@example.com>")
	payloads: list[dict] = []

	def fake_post(url: str, **kwargs: object) -> FakeResponse:
		payloads.append(kwargs["json"])
		return FakeResponse()

	monkeypatch.setattr(email.httpx, "post", fake_post)
	return payloads


def test_requires_sender_configuration() -> None:
	with pytest.raises(EmailDeliveryError):
		send_photo_email(EmailDelivery(recipient="guest@example.com", guest_name="Ada"))


def test_template_payload_uses_image_variable(
	monkeypatch: pytest.MonkeyPatch, sent_payloads: list[dict]
) -> None:
	monkeypatch.setenv("RESEND_TEMPLATE_ID", "tpl_1")
	monkeypatch.setenv("RESEND_TEMPLATE_IMAGE_VARIABLE", "PHOTO")

	provider_id = send_photo_email(
		EmailDelivery(
			recipient="guest@example.com",
			guest_name="Ada",
			image_url="https://images.example.com/a.jpg",
			session_id="session-1",
		)
	)

	assert provider_id == "email-123"
	assert sent_payloads[0]["template"] == {
		"id": "tpl_1",
		"variables": {
			"GUEST_NAME": "Ada",
			"PHOTO": "https://images.example.com/a.jpg",
			"SESSION_ID": "session-1",
		},
	}


def test_template_requires_session_id(monkeypatch: pytest.MonkeyPatch, sent_payloads: list[dict]) -> None:
	monkeypatch.setenv("RESEND_TEMPLATE_ID", "tpl_1")

	with pytest.raises(EmailDeliveryError):
		send_photo_email(
			EmailDelivery(recipient="guest@example.com", guest_name="Ada", image_url="https://x.test/a.jpg")
		)


def test_rejected_email_raises(monkeypatch: pytest.MonkeyPatch, sent_payloads: list[dict]) -> None:
	def failing_post(url: str, **kwargs: object) -> FakeResponse:
		request = httpx.Request("POST", url)
		raise httpx.HTTPStatusError("bad", request=request, response=httpx.Response(422, request=request, text="nope"))

	monkeypatch.setattr(email.httpx, "post", failing_post)

	with pytest.raises(EmailDeliveryError, match="nope"):
		send_photo_email(EmailDelivery(recipient="guest@example.com", guest_name="Ada"))
