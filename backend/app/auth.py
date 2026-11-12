import os
from secrets import compare_digest

from fastapi import Header, HTTPException, Query


def require_token(
	x_booth_token: str | None = Header(default=None),
	token: str | None = Query(default=None),
) -> None:
	"""Reject requests that lack the operator token when BOOTH_API_TOKEN is set.

	The token is accepted as an X-Booth-Token header or a `token` query parameter,
	because browsers cannot attach headers to <img> requests such as the preview.
	"""
	expected = os.getenv("BOOTH_API_TOKEN", "")
	if not expected:
		return

	provided = x_booth_token or token or ""
	if not compare_digest(provided.encode(), expected.encode()):
		raise HTTPException(status_code=401, detail="A valid booth token is required")
