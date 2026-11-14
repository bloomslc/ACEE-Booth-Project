import pytest
from fastapi.testclient import TestClient

from app import main
from app.camera import CapturedPhoto
from app.database import DatabaseError

EMAIL_BODY = {"name": "Ada", "email": "ada@example.com", "image_url": "http://testserver/images/a.jpg"}


def test_health_does_not_require_token(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
	monkeypatch.setenv("BOOTH_API_TOKEN", "secret")

	assert client.get("/api/v1/health").status_code == 200


def test_protected_routes_reject_missing_or_wrong_token(
	client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
	monkeypatch.setenv("BOOTH_API_TOKEN", "secret")
	monkeypatch.setenv("DEV_BYPASS", "true")

	assert client.post("/api/v1/deliveries/email", json=EMAIL_BODY).status_code == 401
	wrong_token = {"X-Booth-Token": "nope"}
	assert client.post("/api/v1/deliveries/email", json=EMAIL_BODY, headers=wrong_token).status_code == 401
	assert client.post("/api/v1/capture").status_code == 401
	assert client.get("/api/v1/camera/preview").status_code == 401


def test_token_accepted_as_header_or_query(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
	monkeypatch.setenv("BOOTH_API_TOKEN", "secret")
	monkeypatch.setenv("DEV_BYPASS", "true")

	by_header = client.post("/api/v1/deliveries/email", json=EMAIL_BODY, headers={"X-Booth-Token": "secret"})
	by_query = client.post("/api/v1/deliveries/email?token=secret", json=EMAIL_BODY)

	assert by_header.status_code == 200
	assert by_query.json()["status"] == "skipped"


def test_email_rejects_foreign_image_url(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
	monkeypatch.setenv("S3_BUCKET", "bucket")
	monkeypatch.setenv("S3_PUBLIC_BASE_URL", "https://images.example.com")
	monkeypatch.setattr(main, "send_photo_email", lambda delivery: "provider-1")

	foreign = {**EMAIL_BODY, "image_url": "https://evil.example.net/a.jpg"}
	local = {**EMAIL_BODY, "image_url": "http://raspberrypi.local:8080/images/a.jpg"}
	bucket = {**EMAIL_BODY, "image_url": "https://images.example.com/sessions/s/a.jpg"}

	host = {"Host": "raspberrypi.local:8080"}

	assert client.post("/api/v1/deliveries/email", json=foreign, headers=host).status_code == 400
	assert client.post("/api/v1/deliveries/email", json=local, headers=host).status_code == 200
	assert client.post("/api/v1/deliveries/email", json=bucket, headers=host).status_code == 200


def test_cors_origins_default_to_any_and_accept_a_list(monkeypatch: pytest.MonkeyPatch) -> None:
	assert main.allowed_origins() == ["*"]

	monkeypatch.setenv("FRONTEND_ORIGIN", "http://a.local:3000, http://b.local:3000")

	assert main.allowed_origins() == ["http://a.local:3000", "http://b.local:3000"]


def test_capture_url_uses_the_host_the_client_connected_to(
	client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
	monkeypatch.setattr(main, "capture_photo", lambda: CapturedPhoto(local_path=str(tmp_path / "abc.jpg")))

	body = client.post("/api/v1/capture", headers={"Host": "raspberrypi.local:8080"}).json()

	assert body["image_url"] == "http://raspberrypi.local:8080/images/abc.jpg"


def test_database_failure_removes_uploaded_photo(
	client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
	photo = tmp_path / "abc.jpg"
	photo.write_bytes(b"jpeg")
	deleted_keys: list[str] = []

	def failing_create_session(session_id: str) -> None:
		raise DatabaseError("down")

	monkeypatch.setenv("S3_BUCKET", "bucket")
	monkeypatch.setattr(main, "capture_photo", lambda: CapturedPhoto(local_path=str(photo)))
	monkeypatch.setattr(main, "upload_image", lambda path, session_id: "https://images.example.com/x.jpg")
	monkeypatch.setattr(main, "is_configured", lambda: True)
	monkeypatch.setattr(main, "create_session", failing_create_session)
	monkeypatch.setattr(main, "delete_image", deleted_keys.append)

	response = client.post("/api/v1/capture")

	assert response.status_code == 503
	assert len(deleted_keys) == 1 and deleted_keys[0].endswith("/abc.jpg")
	assert not photo.exists()


@pytest.mark.parametrize(
	("env", "image_url"),
	[
		({"S3_ENDPOINT_URL": "https://acct.r2.example.com"}, "https://acct.r2.example.com/bucket/sessions/s/a.jpg"),
		({"S3_REGION": "eu-west-1"}, "https://bucket.s3.eu-west-1.amazonaws.com/sessions/s/a.jpg"),
	],
)
def test_email_accepts_upload_url_without_public_base_url(
	client: TestClient, monkeypatch: pytest.MonkeyPatch, env: dict[str, str], image_url: str
) -> None:
	monkeypatch.setenv("S3_BUCKET", "bucket")
	for name, value in env.items():
		monkeypatch.setenv(name, value)
	monkeypatch.setattr(main, "send_photo_email", lambda delivery: "provider-1")

	response = client.post("/api/v1/deliveries/email", json={**EMAIL_BODY, "image_url": image_url})

	assert response.status_code == 200
