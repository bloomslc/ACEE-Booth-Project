import base64
import os
import subprocess
import tempfile
from threading import Lock
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4


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


def is_dev_bypass() -> bool:
	return os.getenv("DEV_BYPASS", "false").lower() in {
		"1",
		"true",
		"yes",
	}


def _bypass_image_bytes() -> bytes | None:
	if not is_dev_bypass():
		return None

	image_path = _project_path("DEV_BYPASS_IMAGE", "frontend/public/image.jpg")
	try:
		return image_path.read_bytes()
	except OSError as error:
		raise CameraCaptureError(f"The bypass image could not be read: {image_path}") from error


def capture_preview() -> str:
	"""Capture a temporary preview frame without adding it to photo storage."""
	bypass_image = _bypass_image_bytes()
	if bypass_image:
		encoded = base64.b64encode(bypass_image).decode("ascii")
		return f"data:image/jpeg;base64,{encoded}"

	preview_path = Path(tempfile.gettempdir()) / f"portrait-booth-preview-{uuid4().hex}.jpg"
	try:
		with CAMERA_LOCK:
			result = subprocess.run(
				[
					"gphoto2",
					"--capture-preview",
					"--filename",
					str(preview_path),
					"--force-overwrite",
				],
				capture_output=True,
				text=True,
				timeout=15,
			)
	except (FileNotFoundError, subprocess.TimeoutExpired) as error:
		raise CameraCaptureError("gphoto2 could not read the camera preview") from error

	try:
		if result.returncode != 0 or not preview_path.is_file():
			raise CameraCaptureError("The camera preview is unavailable")
		encoded = base64.b64encode(preview_path.read_bytes()).decode("ascii")
	except OSError as error:
		raise CameraCaptureError("The camera preview could not be read") from error
	finally:
		preview_path.unlink(missing_ok=True)

	return f"data:image/jpeg;base64,{encoded}"


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

	return CapturedPhoto(local_path=output_path.as_posix())
