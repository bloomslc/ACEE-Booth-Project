import os
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError


class ImageStorageError(RuntimeError):
	"""Raised when an image cannot be uploaded to object storage."""


def is_configured() -> bool:
	return bool(os.getenv("S3_BUCKET"))


def upload_image(local_path: str, session_id: str) -> str:
	if not is_configured():
		raise ImageStorageError("S3_BUCKET is not configured")

	path = Path(local_path)
	key = f"sessions/{session_id}/{path.name}"
	try:
		client = boto3.client(
			"s3",
			endpoint_url=os.getenv("S3_ENDPOINT_URL") or None,
			region_name=os.getenv("S3_REGION", "us-east-1"),
			aws_access_key_id=os.getenv("S3_ACCESS_KEY_ID"),
			aws_secret_access_key=os.getenv("S3_SECRET_ACCESS_KEY"),
		)
		client.upload_file(
			str(path),
			os.environ["S3_BUCKET"],
			key,
			ExtraArgs={"ContentType": "image/jpeg", "CacheControl": "private, max-age=31536000"},
		)
	except (BotoCoreError, ClientError, OSError, KeyError) as error:
		raise ImageStorageError("The image could not be uploaded") from error

	public_base_url = os.getenv("S3_PUBLIC_BASE_URL")
	if public_base_url:
		return f"{public_base_url.rstrip('/')}/{key}"

	endpoint_url = os.getenv("S3_ENDPOINT_URL")
	if endpoint_url:
		return f"{endpoint_url.rstrip('/')}/{os.environ['S3_BUCKET']}/{key}"

	return f"https://{os.environ['S3_BUCKET']}.s3.{os.getenv('S3_REGION', 'us-east-1')}.amazonaws.com/{key}"