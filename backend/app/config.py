import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRUE_VALUES = {"1", "true", "yes"}


def env_flag(name: str, default: str = "false") -> bool:
	return os.getenv(name, default).strip().lower() in TRUE_VALUES


def is_dev_bypass() -> bool:
	return env_flag("DEV_BYPASS")


def project_path(environment_name: str, default: str) -> Path:
	configured_path = Path(os.getenv(environment_name, default))
	return configured_path if configured_path.is_absolute() else PROJECT_ROOT / configured_path


def is_ftp_mode() -> bool:
	"""FTP mode takes photos from a camera that uploads to this server; DEV_BYPASS overrides it."""
	return os.getenv("CAMERA_MODE", "gphoto2").strip().lower() == "ftp" and not is_dev_bypass()


def camera_mode() -> str:
	if is_dev_bypass():
		return "bypass"
	return "ftp" if is_ftp_mode() else "gphoto2"
