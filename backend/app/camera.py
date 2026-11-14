import logging
import shutil
import signal
import subprocess
import time
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from threading import Condition, Lock, Thread
from uuid import uuid4

from PIL import Image, ImageOps

from .config import is_dev_bypass, project_path

logger = logging.getLogger(__name__)


class CameraCaptureError(RuntimeError):
	"""Raised when the connected camera cannot capture an image."""


@dataclass(frozen=True)
class CapturedPhoto:
	local_path: str | None


CAMERA_LOCK = Lock()
PREVIEW_PROCESS_LOCK = Lock()
ACTIVE_PREVIEW_PROCESS = None


def photo_storage_dir() -> Path:
	return project_path("PHOTO_STORAGE_DIR", "data/images")


def bypass_image_path() -> Path:
	return project_path("DEV_BYPASS_IMAGE", "frontend/public/image.jpg")


def watermark_image_path() -> Path:
	return project_path("WATERMARK_IMAGE_PATH", "backend/watermark.png")


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
		# A negative code from SIGTERM means stop_preview_capture ended it to make way for a capture.
		level = logging.INFO if result_code == -signal.SIGTERM else logging.ERROR
		logger.log(level, "gphoto2 preview returned code=%s output_present=%s", result_code, bool(stdout))
		raise CameraCaptureError("The camera preview is unavailable")

	return stdout


class PreviewHub:
	"""Share one gphoto2 preview loop between all connected preview streams."""

	MAX_CONSECUTIVE_FAILURES = 3
	FRAME_TIMEOUT_SECONDS = 20

	def __init__(self) -> None:
		self._condition = Condition()
		self._thread: Thread | None = None
		self._subscribers = 0
		self._frame: bytes | None = None
		self._sequence = 0
		self._error: CameraCaptureError | None = None

	def open(self) -> Iterator[bytes]:
		"""Join the preview loop and wait for the first frame.

		Raises CameraCaptureError when the camera cannot produce a frame.
		"""
		with self._condition:
			self._subscribers += 1
			if self._thread is None:
				self._frame = None
				self._error = None
				self._thread = Thread(target=self._run, name="camera-preview", daemon=True)
				self._thread.start()

		try:
			frame, sequence = self._wait_for_frame(0)
		except CameraCaptureError:
			self._leave()
			raise
		return self._frames(frame, sequence)

	def _leave(self) -> None:
		with self._condition:
			self._subscribers -= 1

	def _wait_for_frame(self, last_sequence: int) -> tuple[bytes, int]:
		with self._condition:
			has_new_frame = self._condition.wait_for(
				lambda: self._sequence != last_sequence or self._error is not None,
				timeout=self.FRAME_TIMEOUT_SECONDS,
			)
			if self._sequence != last_sequence and self._frame is not None:
				return self._frame, self._sequence
			if self._error is not None:
				raise self._error
			if not has_new_frame:
				raise CameraCaptureError("The camera preview timed out")
			raise CameraCaptureError("The camera preview is unavailable")

	def _frames(self, frame: bytes, sequence: int) -> Iterator[bytes]:
		try:
			while True:
				yield (
					b"--frame\r\n"
					b"Content-Type: image/jpeg\r\n"
					+ f"Content-Length: {len(frame)}\r\n\r\n".encode("ascii")
					+ frame
					+ b"\r\n"
				)
				try:
					frame, sequence = self._wait_for_frame(sequence)
				except CameraCaptureError:
					logger.warning("Preview stream ended because the camera stopped producing frames")
					return
		finally:
			self._leave()

	def _run(self) -> None:
		failures = 0
		while True:
			with self._condition:
				if self._subscribers <= 0:
					self._thread = None
					return

			try:
				frame = capture_preview_frame()
			except CameraCaptureError as error:
				failures += 1
				if failures >= self.MAX_CONSECUTIVE_FAILURES:
					with self._condition:
						self._error = error
						self._thread = None
						self._condition.notify_all()
					return
				time.sleep(0.5)
				continue

			failures = 0
			with self._condition:
				self._frame = frame
				self._sequence += 1
				self._condition.notify_all()
			time.sleep(0.1)


PREVIEW_HUB = PreviewHub()


def preview_stream() -> Iterator[bytes]:
	"""Open a multipart JPEG preview stream that ends when the browser disconnects."""
	return PREVIEW_HUB.open()


def add_watermark(image_path: Path) -> None:
	try:
		with Image.open(image_path) as source:
			image = ImageOps.exif_transpose(source).convert("RGBA")
			if image.width > image.height:
				image = image.rotate(90, expand=True)
			with Image.open(watermark_image_path()) as watermark_source:
				watermark = watermark_source.convert("RGBA")
				watermark_width = max(1, image.width // 4)
				watermark_height = max(1, round(watermark.height * watermark_width / watermark.width))
				watermark = watermark.resize(
					(watermark_width, watermark_height),
					Image.Resampling.LANCZOS,
				)

			padding = max(12, image.width // 50)
			position = (padding, image.height - watermark.height - padding)
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


def ingest_uploaded_photo(source: Path) -> CapturedPhoto:
	"""Move a camera-uploaded JPEG into photo storage under a UUID name and watermark it."""
	output_dir = photo_storage_dir()
	output_dir.mkdir(parents=True, exist_ok=True)
	output_path = output_dir / f"{uuid4().hex}.jpg"

	try:
		shutil.move(source, output_path)
	except OSError as error:
		logger.exception("Uploaded photo could not be moved path=%s", source)
		raise CameraCaptureError("The uploaded photo could not be read") from error

	try:
		add_watermark(output_path)
	except CameraCaptureError:
		output_path.unlink(missing_ok=True)
		raise

	return CapturedPhoto(local_path=output_path.as_posix())
