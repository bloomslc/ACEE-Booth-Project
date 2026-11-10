import os
import logging
import subprocess
import time
from threading import Lock
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from PIL import Image

logger = logging.getLogger(__name__)


class CameraCaptureError(RuntimeError):
	"""Raised when the connected camera cannot capture an image."""


@dataclass(frozen=True)
class CapturedPhoto:
	local_path: str | None


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CAMERA_LOCK = Lock()
PREVIEW_PROCESS_LOCK = Lock()
ACTIVE_PREVIEW_PROCESS = None


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
	configured_value = os.getenv("DEV_BYPASS", "false")
	is_enabled = configured_value.lower() in {
		"1",
		"true",
		"yes",
	}
	logger.info("Camera development bypass=%s configured_value=%s", is_enabled, configured_value)
	return is_enabled


def _bypass_image_bytes() -> bytes | None:
	if not is_dev_bypass():
		return None

	image_path = bypass_image_path()
	try:
		return image_path.read_bytes()
	except OSError as error:
		raise CameraCaptureError(f"The bypass image could not be read: {image_path}") from error


def stop_preview_capture() -> None:
	global ACTIVE_PREVIEW_PROCESS
	with PREVIEW_PROCESS_LOCK:
		process = ACTIVE_PREVIEW_PROCESS

	if process is None or process.poll() is not None:
		return

	logger.info("Stopping active camera preview process pid=%s", process.pid)
	process.terminate()
	try:
		process.wait(timeout=1)
	except subprocess.TimeoutExpired:
		logger.warning("Camera preview process did not stop gracefully; killing pid=%s", process.pid)
		process.kill()
		process.wait()


def capture_preview_frame() -> bytes:
	"""Capture one temporary preview JPEG without adding it to photo storage."""
	bypass_image = _bypass_image_bytes()
	if bypass_image:
		return bypass_image

	global ACTIVE_PREVIEW_PROCESS
	process = None
	try:
		with CAMERA_LOCK:
			process = subprocess.Popen(
				[
					"gphoto2",
					"--capture-preview",
					"--stdout",
				],
				stdout=subprocess.PIPE,
				stderr=subprocess.PIPE,
			)
			with PREVIEW_PROCESS_LOCK:
				ACTIVE_PREVIEW_PROCESS = process
			stdout, _ = process.communicate(timeout=15)
			result_code = process.returncode
	except (FileNotFoundError, subprocess.TimeoutExpired) as error:
		logger.exception("gphoto2 preview command failed")
		if process is not None and process.poll() is None:
			process.kill()
			process.wait()
		raise CameraCaptureError("gphoto2 could not read the camera preview") from error
	finally:
		with PREVIEW_PROCESS_LOCK:
			if ACTIVE_PREVIEW_PROCESS is process:
				ACTIVE_PREVIEW_PROCESS = None

	if result_code != 0 or not stdout:
		logger.error("gphoto2 preview returned code=%s output_present=%s", result_code, bool(stdout))
		raise CameraCaptureError("The camera preview is unavailable")

	return stdout


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
		logger.exception("Watermarking failed for image path=%s", image_path)
		raise CameraCaptureError("The captured photo could not be watermarked") from error


def capture_photo() -> CapturedPhoto:
	"""Capture and persist a JPEG, returning its local path."""
	logger.info("Starting camera capture dev_bypass=%s", is_dev_bypass())
	stop_preview_capture()
	bypass_image = _bypass_image_bytes()
	if bypass_image:
		logger.info("Using development bypass image path=%s", bypass_image_path())
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
	except FileNotFoundError as error:
		logger.exception("gphoto2 was not found while capturing image")
		raise CameraCaptureError("gphoto2 is not installed or not available on PATH") from error
	except subprocess.TimeoutExpired as error:
		logger.exception("gphoto2 capture timed out after 60 seconds")
		raise CameraCaptureError("gphoto2 could not capture a photo") from error

	if result.returncode != 0 or not output_path.is_file():
		stderr = (result.stderr or "").strip()
		stdout = (result.stdout or "").strip()
		logger.error(
			"gphoto2 capture failed returncode=%s output_path=%s stderr=%s stdout=%s",
			result.returncode,
			output_path,
			stderr[-1000:],
			stdout[-1000:],
		)
		output_path.unlink(missing_ok=True)
		detail = stderr or stdout or "no gphoto2 diagnostics"
		raise CameraCaptureError(f"The camera did not return a photo: {detail[-500:]}")

	try:
		add_watermark(output_path)
	except CameraCaptureError:
		output_path.unlink(missing_ok=True)
		raise

	return CapturedPhoto(local_path=output_path.as_posix())
