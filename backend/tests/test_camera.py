import pytest
from PIL import Image

from app import camera
from app.camera import CameraCaptureError, add_watermark


def test_landscape_photo_becomes_portrait_and_is_watermarked(
	monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
	photo = tmp_path / "photo.jpg"
	watermark = tmp_path / "watermark.png"
	Image.new("RGB", (400, 200), "white").save(photo)
	Image.new("RGBA", (100, 50), (255, 0, 0, 255)).save(watermark)
	monkeypatch.setenv("WATERMARK_IMAGE_PATH", str(watermark))

	add_watermark(photo)

	with Image.open(photo) as result:
		assert result.size == (200, 400)
		red, green, blue = result.getpixel((20, 380))
		assert red > 200 and green < 80 and blue < 80


def test_missing_watermark_raises(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
	photo = tmp_path / "photo.jpg"
	Image.new("RGB", (100, 200), "white").save(photo)
	monkeypatch.setenv("WATERMARK_IMAGE_PATH", str(tmp_path / "missing.png"))

	with pytest.raises(CameraCaptureError):
		add_watermark(photo)


@pytest.fixture
def fast_hub(monkeypatch: pytest.MonkeyPatch) -> camera.PreviewHub:
	monkeypatch.setattr(camera.time, "sleep", lambda seconds: None)
	return camera.PreviewHub()


def test_preview_hub_shares_frames_and_stops_when_unsubscribed(
	monkeypatch: pytest.MonkeyPatch, fast_hub: camera.PreviewHub
) -> None:
	monkeypatch.setattr(camera, "capture_preview_frame", lambda: b"jpeg-bytes")

	first = fast_hub.open()
	second = fast_hub.open()

	assert b"jpeg-bytes" in next(first)
	assert b"jpeg-bytes" in next(second)
	first.close()
	second.close()
	fast_hub._thread.join(timeout=2)
	assert fast_hub._subscribers == 0


def test_preview_hub_raises_when_camera_keeps_failing(
	monkeypatch: pytest.MonkeyPatch, fast_hub: camera.PreviewHub
) -> None:
	def failing_frame() -> bytes:
		raise CameraCaptureError("no camera")

	monkeypatch.setattr(camera, "capture_preview_frame", failing_frame)

	with pytest.raises(CameraCaptureError, match="no camera"):
		fast_hub.open()
	assert fast_hub._subscribers == 0
