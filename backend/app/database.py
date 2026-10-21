import os
from contextlib import contextmanager
from typing import Iterator

import psycopg
from psycopg import Connection


class DatabaseError(RuntimeError):
	"""Raised when the booth database cannot be reached or updated."""


def is_configured() -> bool:
	dev_bypass = os.getenv("DEV_BYPASS", "false")
	return bool(os.getenv("NEON_DATABASE_URL")) and dev_bypass.lower() not in {"1", "true", "yes"}


def _connection() -> Connection:
	if not is_configured():
		raise DatabaseError("Neon database is not configured")

	try:
		return psycopg.connect(os.environ["NEON_DATABASE_URL"], connect_timeout=5)
	except (KeyError, psycopg.Error) as error:
		raise DatabaseError("Could not connect to Neon") from error


@contextmanager
def connection() -> Iterator[Connection]:
	db = _connection()
	try:
		yield db
	finally:
		db.close()


def initialize() -> None:
	if not is_configured():
		return

	statements = (
		"""
		CREATE TABLE IF NOT EXISTS sessions (
			id TEXT PRIMARY KEY,
			status TEXT NOT NULL DEFAULT 'created',
			created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
			updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
		)
		""",
		"""
		CREATE TABLE IF NOT EXISTS photos (
			id BIGSERIAL PRIMARY KEY,
			session_id TEXT NOT NULL,
			local_path TEXT NOT NULL,
			remote_url TEXT NULL,
			created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
			CONSTRAINT photos_session_fk FOREIGN KEY (session_id) REFERENCES sessions(id)
		)
		""",
		"""
		CREATE TABLE IF NOT EXISTS deliveries (
			id BIGSERIAL PRIMARY KEY,
			session_id TEXT NULL,
			recipient VARCHAR(320) NOT NULL,
			provider_id TEXT NOT NULL,
			status TEXT NOT NULL,
			created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
			CONSTRAINT deliveries_session_fk FOREIGN KEY (session_id) REFERENCES sessions(id)
		)
		""",
	)
	try:
		with connection() as db:
			with db.cursor() as cursor:
				for statement in statements:
					cursor.execute(statement)
			db.commit()
	except psycopg.Error as error:
		raise DatabaseError("Could not initialize Neon tables") from error


def create_session(session_id: str) -> None:
	with connection() as db:
		with db.cursor() as cursor:
			cursor.execute("INSERT INTO sessions (id) VALUES (%s)", (session_id,))
		db.commit()


def record_photo(session_id: str, local_path: str, remote_url: str | None) -> None:
	with connection() as db:
		with db.cursor() as cursor:
			cursor.execute(
				"INSERT INTO photos (session_id, local_path, remote_url) VALUES (%s, %s, %s)",
				(session_id, local_path, remote_url),
			)
			cursor.execute(
				"UPDATE sessions SET status = 'captured', updated_at = NOW() WHERE id = %s",
				(session_id,),
			)
		db.commit()


def record_delivery(
	session_id: str | None,
	recipient: str,
	provider_id: str,
	status: str = "sent",
) -> None:
	with connection() as db:
		with db.cursor() as cursor:
			cursor.execute(
				"""INSERT INTO deliveries
				(session_id, recipient, provider_id, status)
				VALUES (%s, %s, %s, %s)""",
				(session_id, recipient, provider_id, status),
			)
			if session_id:
				cursor.execute(
					"UPDATE sessions SET status = 'delivered', updated_at = NOW() WHERE id = %s",
					(session_id,),
				)
		db.commit()
