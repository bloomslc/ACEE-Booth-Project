import os
import tempfile

# Must be set before app.main is imported, because it creates the storage directory on import.
os.environ["PHOTO_STORAGE_DIR"] = tempfile.mkdtemp(prefix="booth-images-")

import pytest
from fastapi.testclient import TestClient

from app.main import app

CONFIGURED_VARIABLES = (
	"CAMERA_MODE",
	"FTP_CAPTURE_TIMEOUT",
	"BOOTH_API_TOKEN",
	"DEV_BYPASS",
	"FRONTEND_ORIGIN",
	"NEON_DATABASE_URL",
	"RESEND_API_KEY",
	"RESEND_FROM_EMAIL",
	"RESEND_TEMPLATE_ID",
	"RESEND_TEMPLATE_IMAGE_VARIABLE",
	"S3_BUCKET",
	"S3_ENDPOINT_URL",
	"S3_REGION",
	"S3_PUBLIC_BASE_URL",
)


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
	for name in CONFIGURED_VARIABLES:
		monkeypatch.delenv(name, raising=False)


@pytest.fixture
def client() -> TestClient:
	return TestClient(app)
