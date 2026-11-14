import logging
import os
import threading
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import ThreadedFTPServer

from .config import project_path

logger = logging.getLogger(__name__)

JPEG_SUFFIXES = {".jpg", ".jpeg"}
MAX_PENDING_UPLOADS = 20


class FtpConfigurationError(RuntimeError):
	"""Raised when FTP mode is enabled without usable settings."""


@dataclass(frozen=True)
class Upload:
	sequence: int
	path: Path


def upload_dir() -> Path:
	return project_path("FTP_UPLOAD_DIR", "data/ftp-incoming")


def _passive_ports() -> range:
	configured = os.getenv("FTP_PASSIVE_PORTS", "60000-60010")
	try:
		first, last = (int(part) for part in configured.split("-", 1))
	except ValueError as error:
		raise FtpConfigurationError("FTP_PASSIVE_PORTS must look like 60000-60010") from error
	return range(first, last + 1)


class UploadInbox:
	"""Thread-safe list of finished camera uploads that no capture request has claimed yet."""

	def __init__(self) -> None:
		self._lock = threading.Lock()
		self._pending: deque[Upload] = deque(maxlen=MAX_PENDING_UPLOADS)
		self._sequence = 0
		self._waiters = 0
		self._generation = 0

	def begin_wait(self) -> int:
		"""Register a capture request that is waiting; the newest waiter supersedes older ones."""
		with self._lock:
			self._waiters += 1
			self._generation += 1
			return self._generation

	def end_wait(self) -> None:
		with self._lock:
			self._waiters = max(0, self._waiters - 1)

	def is_latest_waiter(self, generation: int) -> bool:
		with self._lock:
			return generation == self._generation

	def waiting(self) -> bool:
		with self._lock:
			return self._waiters > 0

	def add(self, path: Path) -> Upload:
		with self._lock:
			self._sequence += 1
			upload = Upload(self._sequence, path)
			self._pending.append(upload)
			return upload

	def latest_sequence(self) -> int:
		with self._lock:
			return self._sequence

	def claim_after(self, sequence: int) -> Upload | None:
		"""Remove and return the oldest upload newer than `sequence`, so only one request gets each photo."""
		with self._lock:
			for upload in self._pending:
				if upload.sequence > sequence:
					self._pending.remove(upload)
					return upload
		return None


INBOX = UploadInbox()


class FtpReceiver:
	"""Embedded FTP server that a camera uploads finished JPEGs to."""

	def __init__(self, inbox: UploadInbox) -> None:
		self._inbox = inbox
		self._server: ThreadedFTPServer | None = None
		self._thread: threading.Thread | None = None
		self._stopping = False
		self._state_lock = threading.Lock()
		self._clients = 0
		self._last_login: float | None = None
		self._last_login_failure: float | None = None
		self._last_upload: tuple[str, float, bool] | None = None

	def status(self) -> dict[str, object]:
		"""Snapshot of what the camera has done, with ages in seconds so clocks never need to match."""
		now = time.monotonic()

		def age(moment: float | None) -> int | None:
			return None if moment is None else round(now - moment)

		with self._state_lock:
			last_upload = None
			if self._last_upload:
				name, moment, used = self._last_upload
				last_upload = {"name": name, "seconds_ago": age(moment), "used": used}
			return {
				"running": self._server is not None,
				"port": self.port,
				"clients": self._clients,
				"last_login_seconds_ago": age(self._last_login),
				"last_login_failed_seconds_ago": age(self._last_login_failure),
				"last_upload": last_upload,
			}

	def _record(self, **changes: object) -> None:
		with self._state_lock:
			for name, value in changes.items():
				setattr(self, name, value)

	def _adjust_clients(self, delta: int) -> None:
		with self._state_lock:
			self._clients = max(0, self._clients + delta)

	@property
	def port(self) -> int | None:
		return self._server.address[1] if self._server else None

	def start(
		self,
		host: str = "0.0.0.0",
		port: int = 2121,
		user: str = "booth",
		password: str = "",
		directory: Path | None = None,
		passive_ports: range | None = None,
		masquerade_address: str | None = None,
	) -> None:
		if not password:
			raise FtpConfigurationError("FTP_PASSWORD must be set when CAMERA_MODE=ftp")

		root = directory or upload_dir()
		root.mkdir(parents=True, exist_ok=True)

		# Write-only for the camera: it may create folders and upload, but not read or delete files.
		authorizer = DummyAuthorizer()
		authorizer.add_user(user, password, str(root), perm="elwmf")

		inbox = self._inbox
		receiver = self

		class CameraHandler(FTPHandler):
			def on_connect(self) -> None:
				receiver._adjust_clients(1)
				logger.info("Camera connected from %s", self.remote_ip)

			def on_disconnect(self) -> None:
				receiver._adjust_clients(-1)

			def on_login(self, username: str) -> None:
				receiver._record(_last_login=time.monotonic())
				logger.info("Camera logged in user=%s", username)

			def on_login_failed(self, username: str, password: str) -> None:
				receiver._record(_last_login_failure=time.monotonic())
				logger.warning("Camera login failed user=%s", username)

			def on_incomplete_file_received(self, file: str) -> None:
				logger.warning("Camera upload was interrupted name=%s", Path(file).name)
				Path(file).unlink(missing_ok=True)

			def on_file_received(self, file: str) -> None:
				path = Path(file)
				is_jpeg = path.suffix.lower() in JPEG_SUFFIXES
				receiver._record(_last_upload=(path.name, time.monotonic(), is_jpeg))
				if not is_jpeg:
					logger.info("Ignoring non-JPEG FTP upload name=%s", path.name)
					return
				upload = inbox.add(path)
				logger.info("Camera upload received sequence=%s name=%s", upload.sequence, path.name)

		CameraHandler.authorizer = authorizer
		CameraHandler.passive_ports = passive_ports or _passive_ports()
		CameraHandler.masquerade_address = masquerade_address
		CameraHandler.banner = "ACEE booth FTP ready"

		self._stopping = False
		self._server = ThreadedFTPServer((host, port), CameraHandler)
		self._thread = threading.Thread(target=self._serve, name="camera-ftp", daemon=True)
		self._thread.start()
		logger.info("FTP server listening host=%s port=%s directory=%s", host, self.port, root)

	def _serve(self) -> None:
		try:
			self._server.serve_forever()
		except OSError:
			# close_all() closes the poller while the loop is waiting on it; that is expected during stop().
			if not self._stopping:
				raise

	def stop(self) -> None:
		if self._server is None:
			return
		self._stopping = True
		self._server.close_all()
		if self._thread is not None:
			self._thread.join(timeout=5)
		self._server = None
		self._thread = None


RECEIVER = FtpReceiver(INBOX)


def start_from_environment() -> None:
	try:
		port = int(os.getenv("FTP_PORT", "2121"))
	except ValueError as error:
		raise FtpConfigurationError("FTP_PORT must be a number") from error

	RECEIVER.start(
		host=os.getenv("FTP_HOST", "0.0.0.0"),
		port=port,
		user=os.getenv("FTP_USER", "booth"),
		password=os.getenv("FTP_PASSWORD", ""),
		masquerade_address=os.getenv("FTP_MASQUERADE_ADDRESS") or None,
	)
