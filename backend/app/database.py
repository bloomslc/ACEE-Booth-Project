import os
from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache

import psycopg
from psycopg import Connection
from psycopg_pool import ConnectionPool, PoolTimeout

from .config import is_dev_bypass


class DatabaseError(RuntimeError):
	"""Raised when the booth database cannot be reached or updated."""


def is_configured() -> bool:
	return bool(os.getenv("NEON_DATABASE_URL")) and not is_dev_bypass()


@lru_cache(maxsize=1)
def _pool() -> ConnectionPool:
	if not is_configured():
		raise DatabaseError("Neon database is not configured")

	pool = ConnectionPool(
		os.environ["NEON_DATABASE_URL"],
		min_size=1,
		max_size=4,
		kwargs={"connect_timeout": 5},
		check=ConnectionPool.check_connection,
		open=False,
	)
	try:
		pool.open(wait=True, timeout=10)
	except PoolTimeout as error:
		pool.close()
		raise DatabaseError("Could not connect to Neon") from error
	return pool


@contextmanager
def connection() -> Iterator[Connection]:
	try:
		with _pool().connection(timeout=10) as db:
			yield db
	except (PoolTimeout, psycopg.OperationalError) as error:
		raise DatabaseError("Could not connect to Neon") from error
	except psycopg.Error as error:
		raise DatabaseError("The booth database could not complete the request") from error


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
	with connection() as db:
		with db.cursor() as cursor:
			for statement in statements:
				cursor.execute(statement)
		db.commit()


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
