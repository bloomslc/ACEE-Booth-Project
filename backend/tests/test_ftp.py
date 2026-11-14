import ftplib
import io
import threading
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main
from app.camera import CapturedPhoto
from app.ftp import INBOX, FtpConfigurationError, FtpReceiver, UploadInbox


def wait_until(condition, timeout: float = 5.0) -> bool:
	deadline = time.monotonic() + timeout
	while time.monotonic() < deadline:
		if condition():
			return True
		time.sleep(0.05)
	return False


def test_inbox_hands_each_upload_to_one_claimant_and_skips_old_ones(tmp_path: Path) -> None:
	inbox = UploadInbox()
	before = inbox.add(tmp_path / "old.jpg")

	assert inbox.claim_after(before.sequence) is None

	newer = inbox.add(tmp_path / "new.jpg")

	assert inbox.claim_after(before.sequence) == newer
	assert inbox.claim_after(before.sequence) is None


def test_receiver_requires_a_password(tmp_path: Path) -> None:
	with pytest.raises(FtpConfigurationError):
		FtpReceiver(UploadInbox()).start(password="", directory=tmp_path)


def test_receiver_queues_jpegs_and_ignores_other_files(tmp_path: Path) -> None:
	inbox = UploadInbox()
	receiver = FtpReceiver(inbox)
	receiver.start(
		host="127.0.0.1",
		port=0,
		user="booth",
		password="pw",
		directory=tmp_path,
		passive_ports=range(50200, 50220),
	)
	try:
		with ftplib.FTP() as client:
			client.connect("127.0.0.1", receiver.port, timeout=5)
			client.login("booth", "pw")
			client.storbinary("STOR DSC00001.ARW", io.BytesIO(b"raw"))
			client.storbinary("STOR DSC00001.JPG", io.BytesIO(b"jpeg"))

		assert wait_until(lambda: inbox.latest_sequence() == 1)
		upload = inbox.claim_after(0)
		assert upload is not None and upload.path.name == "DSC00001.JPG"
		assert upload.path.read_bytes() == b"jpeg"
	finally:
		receiver.stop()


def test_receiver_rejects_wrong_password(tmp_path: Path) -> None:
	receiver = FtpReceiver(UploadInbox())
	receiver.start(host="127.0.0.1", port=0, password="pw", directory=tmp_path, passive_ports=range(50220, 50240))
	try:
		with ftplib.FTP() as client:
			client.connect("127.0.0.1", receiver.port, timeout=5)
			with pytest.raises(ftplib.error_perm):
				client.login("booth", "wrong")
	finally:
		receiver.stop()


def test_capture_waits_for_the_next_camera_upload(
	client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
	monkeypatch.setenv("CAMERA_MODE", "ftp")
	monkeypatch.setenv("FTP_CAPTURE_TIMEOUT", "5")
	ingested: list[Path] = []

	def fake_ingest(path: Path) -> CapturedPhoto:
		ingested.append(path)
		return CapturedPhoto(local_path=str(tmp_path / "abc.jpg"))

	monkeypatch.setattr(main, "ingest_uploaded_photo", fake_ingest)
	INBOX.add(tmp_path / "taken-before-the-request.jpg")
	shot = tmp_path / "DSC00002.JPG"
	threading.Timer(0.5, INBOX.add, args=(shot,)).start()

	response = client.post("/api/v1/capture")

	assert response.status_code == 200
	assert response.json()["image_url"].endswith("/images/abc.jpg")
	assert ingested == [shot]


def test_capture_times_out_when_no_photo_arrives(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
	monkeypatch.setenv("CAMERA_MODE", "ftp")
	monkeypatch.setenv("FTP_CAPTURE_TIMEOUT", "0.3")

	assert client.post("/api/v1/capture").status_code == 408


def test_ftp_mode_has_no_preview_and_reports_mode(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
	monkeypatch.setenv("CAMERA_MODE", "ftp")

	assert client.get("/api/v1/camera/preview").status_code == 404
	assert client.get("/api/v1/health").json()["camera_mode"] == "ftp"


def test_dev_bypass_overrides_ftp_mode(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
	monkeypatch.setenv("CAMERA_MODE", "ftp")
	monkeypatch.setenv("DEV_BYPASS", "true")

	assert client.get("/api/v1/health").json()["camera_mode"] == "bypass"
