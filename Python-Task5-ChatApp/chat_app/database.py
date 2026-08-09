"""SQLite user, room, and message repository."""

from __future__ import annotations

import re
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from .errors import AlreadyExistsError, NotFoundError, ValidationError
from .models import Message, Room, User
from .security import hash_password, verify_password


DEFAULT_DATABASE_PATH = Path(__file__).resolve().parents[1] / "chat.db"
USERNAME_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_]{2,19}")
ROOM_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9 _-]{0,39}")
MAX_MESSAGE_LENGTH = 2_000


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def validate_username(username: str) -> str:
    cleaned = username.strip()
    if not USERNAME_PATTERN.fullmatch(cleaned):
        raise ValidationError(
            "Username must be 3–20 characters, start with a letter, and use only letters, numbers, or underscores."
        )
    return cleaned


def validate_room_name(name: str) -> str:
    cleaned = " ".join(name.strip().split())
    if not ROOM_PATTERN.fullmatch(cleaned):
        raise ValidationError(
            "Room name must be 1–40 characters using letters, numbers, spaces, hyphens, or underscores."
        )
    return cleaned


def validate_message(text: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        raise ValidationError("Message cannot be empty.")
    if len(cleaned) > MAX_MESSAGE_LENGTH:
        raise ValidationError(
            f"Message cannot exceed {MAX_MESSAGE_LENGTH} characters."
        )
    return cleaned


class ChatDatabase:
    """Thread-safe-by-connection SQLite repository."""

    def __init__(self, path: Path = DEFAULT_DATABASE_PATH) -> None:
        self.path = Path(path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as connection, connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL COLLATE NOCASE UNIQUE,
                    password_salt BLOB NOT NULL,
                    password_hash BLOB NOT NULL,
                    iterations INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS rooms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL COLLATE NOCASE UNIQUE,
                    created_by INTEGER REFERENCES users(id),
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    room_id INTEGER NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    text TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_messages_room_time
                ON messages(room_id, created_at, id);
                """
            )
            connection.execute(
                """
                INSERT OR IGNORE INTO rooms(name, created_by, created_at)
                VALUES('Lobby', NULL, ?)
                """,
                (utc_timestamp(),),
            )

    def register_user(self, username: str, password: str) -> User:
        username = validate_username(username)
        salt, digest, iterations = hash_password(password)
        try:
            with closing(self._connect()) as connection, connection:
                cursor = connection.execute(
                    """
                    INSERT INTO users(
                        username, password_salt, password_hash, iterations, created_at
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (username, salt, digest, iterations, utc_timestamp()),
                )
                user_id = int(cursor.lastrowid)
        except sqlite3.IntegrityError as error:
            raise AlreadyExistsError("That username is already registered.") from error
        return User(user_id, username)

    def authenticate(self, username: str, password: str) -> User | None:
        username = username.strip()
        with closing(self._connect()) as connection:
            row = connection.execute(
                """
                SELECT id, username, password_salt, password_hash, iterations
                FROM users WHERE username = ? COLLATE NOCASE
                """,
                (username,),
            ).fetchone()
        if row is None:
            return None
        if not verify_password(
            password,
            bytes(row["password_salt"]),
            bytes(row["password_hash"]),
            int(row["iterations"]),
        ):
            return None
        return User(int(row["id"]), str(row["username"]))

    def list_rooms(self) -> list[Room]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT rooms.id, rooms.name, COUNT(messages.id) AS message_count
                FROM rooms
                LEFT JOIN messages ON messages.room_id = rooms.id
                GROUP BY rooms.id, rooms.name
                ORDER BY rooms.name COLLATE NOCASE
                """
            ).fetchall()
        return [
            Room(int(row["id"]), str(row["name"]), int(row["message_count"]))
            for row in rows
        ]

    def get_room(self, room_id: int) -> Room:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT id, name FROM rooms WHERE id = ?",
                (room_id,),
            ).fetchone()
        if row is None:
            raise NotFoundError("That chat room no longer exists.")
        return Room(int(row["id"]), str(row["name"]))

    def create_room(self, name: str, created_by: int) -> Room:
        name = validate_room_name(name)
        try:
            with closing(self._connect()) as connection, connection:
                cursor = connection.execute(
                    """
                    INSERT INTO rooms(name, created_by, created_at)
                    VALUES (?, ?, ?)
                    """,
                    (name, created_by, utc_timestamp()),
                )
                room_id = int(cursor.lastrowid)
        except sqlite3.IntegrityError as error:
            raise AlreadyExistsError("A room with that name already exists.") from error
        return Room(room_id, name)

    def save_message(self, room_id: int, user: User, text: str) -> Message:
        text = validate_message(text)
        timestamp = utc_timestamp()
        try:
            with closing(self._connect()) as connection, connection:
                cursor = connection.execute(
                    """
                    INSERT INTO messages(room_id, user_id, text, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (room_id, user.id, text, timestamp),
                )
                message_id = int(cursor.lastrowid)
        except sqlite3.IntegrityError as error:
            raise NotFoundError("The room or user no longer exists.") from error
        return Message(message_id, room_id, user.username, text, timestamp)

    def get_history(self, room_id: int, limit: int = 100) -> list[Message]:
        limit = max(1, min(limit, 500))
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT m.id, m.room_id, u.username, m.text, m.created_at
                FROM messages AS m
                JOIN users AS u ON u.id = m.user_id
                WHERE m.room_id = ?
                ORDER BY m.created_at DESC, m.id DESC
                LIMIT ?
                """,
                (room_id, limit),
            ).fetchall()
        messages = [
            Message(
                id=int(row["id"]),
                room_id=int(row["room_id"]),
                username=str(row["username"]),
                text=str(row["text"]),
                timestamp=str(row["created_at"]),
            )
            for row in rows
        ]
        messages.reverse()
        return messages
