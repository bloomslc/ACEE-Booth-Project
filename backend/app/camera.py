import os
import subprocess
import time
from threading import Lock
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from PIL import Image


class CameraCaptureError(RuntimeError):
	"""Raised when the connected camera cannot capture an image."""


@dataclass(frozen=True)
class CapturedPhoto:
	local_path: str | None


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CAMERA_LOCK = Lock()


def _project_path(environment_name: str, default: str) -> Path:
	configured_path = Path(os.getenv(environment_name, default))
	return configured_path if configured_path.is_absolute() else PROJECT_ROOT / configured_path


def photo_storage_dir() -> Path:
	return _project_path("PHOTO_STORAGE_DIR", "data/images")


def bypass_image_path() -> Path:
	return _project_path("DEV_BYPASS_IMAGE", "frontend/public/image.jpg")


def watermark_image_path() -> Path:
	return _project_path("WATERMARK_IMAGE_PATH", "backend/watermark.png")


def is_dev_bypass() -> bool:
	return os.getenv("DEV_BYPASS", "false").lower() in {
		"1",
		"true",
		"yes",
	}


def _bypass_image_bytes() -> bytes | None:
	if not is_dev_bypass():
		return None

	image_path = bypass_image_path()
	try:
		return image_path.read_bytes()
	except OSError as error:
		raise CameraCaptureError(f"The bypass image could not be read: {image_path}") from error


def capture_preview_frame() -> bytes:
	"""Capture one temporary preview JPEG without adding it to photo storage."""
	bypass_image = _bypass_image_bytes()
	if bypass_image:
		return bypass_image

	try:
		with CAMERA_LOCK:
			result = subprocess.run(
				[
					"gphoto2",
					"--capture-preview",
					"--stdout",
				],
				capture_output=True,
				timeout=15,
			)
	except (FileNotFoundError, subprocess.TimeoutExpired) as error:
		raise CameraCaptureError("gphoto2 could not read the camera preview") from error

	if result.returncode != 0 or not result.stdout:
		raise CameraCaptureError("The camera preview is unavailable")

	return result.stdout


def preview_stream(first_frame: bytes):
	"""Yield JPEG preview frames until the browser closes the stream."""
	frame = first_frame
	while True:
		yield (
			b"--frame\r\n"
			b"Content-Type: image/jpeg\r\n"
			+ f"Content-Length: {len(frame)}\r\n\r\n".encode("ascii")
			+ frame
			+ b"\r\n"
		)
		time.sleep(0.1)
		frame = capture_preview_frame()


def add_watermark(image_path: Path) -> None:
	try:
		with Image.open(image_path) as source:
			image = source.convert("RGBA")
			with Image.open(watermark_image_path()) as watermark_source:
				watermark = watermark_source.convert("RGBA")
				watermark_width = max(1, image.width // 6)
				watermark_height = max(1, round(watermark.height * watermark_width / watermark.width))
				watermark = watermark.resize(
					(watermark_width, watermark_height),
					Image.Resampling.LANCZOS,
				)

			padding = max(12, image.width // 50)
			position = (
				image.width - watermark.width - padding,
				image.height - watermark.height - padding,
			)
			image.alpha_composite(watermark, position)
			image.convert("RGB").save(image_path, "JPEG", quality=95, optimize=True)
	except (OSError, ValueError) as error:
		raise CameraCaptureError("The captured photo could not be watermarked") from error


def capture_photo() -> CapturedPhoto:
	"""Capture and persist a JPEG, returning its local path."""
	bypass_image = _bypass_image_bytes()
	if bypass_image:
		return CapturedPhoto(local_path=None)

	output_dir = photo_storage_dir()
	output_dir.mkdir(parents=True, exist_ok=True)
	output_path = output_dir / f"{uuid4().hex}.jpg"

	try:
		with CAMERA_LOCK:
			result = subprocess.run(
				[
					"gphoto2",
					"--capture-image-and-download",
					"--filename",
					str(output_path),
					"--force-overwrite",
				],
				capture_output=True,
				text=True,
				timeout=60,
			)
	except (FileNotFoundError, subprocess.TimeoutExpired) as error:
		raise CameraCaptureError("gphoto2 could not capture a photo") from error

	if result.returncode != 0 or not output_path.is_file():
		output_path.unlink(missing_ok=True)
		raise CameraCaptureError("The camera did not return a photo")

	try:
		add_watermark(output_path)
	except CameraCaptureError:
		output_path.unlink(missing_ok=True)
		raise

	return CapturedPhoto(local_path=output_path.as_posix())
