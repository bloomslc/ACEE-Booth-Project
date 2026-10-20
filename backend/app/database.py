import os
from contextlib import contextmanager
from typing import Iterator

import mysql.connector
from mysql.connector.abstracts import MySQLConnectionAbstract
from mysql.connector.pooling import PooledMySQLConnection

Connection = MySQLConnectionAbstract | PooledMySQLConnection


class DatabaseError(RuntimeError):
	"""Raised when the booth database cannot be reached or updated."""


def is_configured() -> bool:
	return bool(os.getenv("MYSQL_HOST"))


def _connection() -> Connection:
	if not is_configured():
		raise DatabaseError("MySQL is not configured")

	try:
		return mysql.connector.connect(
			host=os.getenv("MYSQL_HOST"),
		port=int(os.getenv("MYSQL_PORT", "3306")),
		user=os.getenv("MYSQL_USER"),
		password=os.getenv("MYSQL_PASSWORD"),
		database=os.getenv("MYSQL_DATABASE"),
		connection_timeout=5,
		)
	except mysql.connector.Error as error:
		raise DatabaseError("Could not connect to MySQL") from error


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
			id CHAR(36) PRIMARY KEY,
			status VARCHAR(32) NOT NULL DEFAULT 'created',
			created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
			updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
		)
		""",
		"""
		CREATE TABLE IF NOT EXISTS photos (
			id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
			session_id CHAR(36) NOT NULL,
			image_data_url LONGTEXT NOT NULL,
			created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
			CONSTRAINT photos_session_fk FOREIGN KEY (session_id) REFERENCES sessions(id)
		)
		""",
		"""
		CREATE TABLE IF NOT EXISTS deliveries (
			id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
			session_id CHAR(36) NULL,
			recipient VARCHAR(320) NOT NULL,
			provider_id VARCHAR(255) NOT NULL,
			status VARCHAR(32) NOT NULL,
			created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
			CONSTRAINT deliveries_session_fk FOREIGN KEY (session_id) REFERENCES sessions(id)
		)
		""",
	)

	try:
		with connection() as db:
			cursor = db.cursor()
			for statement in statements:
				cursor.execute(statement)
			db.commit()
			cursor.close()
	except mysql.connector.Error as error:
		raise DatabaseError("Could not initialize MySQL tables") from error


def create_session(session_id: str) -> None:
	with connection() as db:
		cursor = db.cursor()
		cursor.execute("INSERT INTO sessions (id) VALUES (%s)", (session_id,))
		db.commit()
		cursor.close()


def record_photo(session_id: str, image_data_url: str) -> None:
	with connection() as db:
		cursor = db.cursor()
		cursor.execute(
			"INSERT INTO photos (session_id, image_data_url) VALUES (%s, %s)",
			(session_id, image_data_url),
		)
		cursor.execute(
			"UPDATE sessions SET status = 'captured' WHERE id = %s",
			(session_id,),
		)
		db.commit()
		cursor.close()


def record_delivery(
	session_id: str | None,
	recipient: str,
	provider_id: str,
	status: str = "sent",
) -> None:
	with connection() as db:
		cursor = db.cursor()
		cursor.execute(
			"""INSERT INTO deliveries
			(session_id, recipient, provider_id, status)
			VALUES (%s, %s, %s, %s)""",
			(session_id, recipient, provider_id, status),
		)
		if session_id:
			cursor.execute(
				"UPDATE sessions SET status = 'delivered' WHERE id = %s",
				(session_id,),
			)
		db.commit()
		cursor.close()
