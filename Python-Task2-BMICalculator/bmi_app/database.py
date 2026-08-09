"""SQLite persistence for BMI history."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from .logic import BMIResult


DATABASE_PATH = Path(__file__).resolve().parents[1] / "bmi_history.db"


class BMIDatabase:
    """Store and retrieve BMI measurements using short-lived connections."""

    def __init__(self, path: Path = DATABASE_PATH) -> None:
        self.path = path
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as connection, connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS bmi_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_name TEXT NOT NULL COLLATE NOCASE,
                    weight_kg REAL NOT NULL CHECK (weight_kg > 0),
                    height_m REAL NOT NULL CHECK (height_m > 0),
                    bmi REAL NOT NULL CHECK (bmi > 0),
                    category TEXT NOT NULL,
                    recorded_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_bmi_user_time
                ON bmi_records (user_name COLLATE NOCASE, recorded_at)
                """
            )

    def save_record(
        self,
        user_name: str,
        weight_kg: float,
        height_m: float,
        result: BMIResult,
    ) -> None:
        timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
        with closing(self._connect()) as connection, connection:
            connection.execute(
                """
                INSERT INTO bmi_records
                    (user_name, weight_kg, height_m, bmi, category, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user_name,
                    weight_kg,
                    height_m,
                    result.bmi,
                    result.category,
                    timestamp,
                ),
            )

    def get_users(self) -> list[str]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT MIN(user_name) AS user_name
                FROM bmi_records
                GROUP BY user_name COLLATE NOCASE
                ORDER BY user_name COLLATE NOCASE
                """
            ).fetchall()
        return [str(row["user_name"]) for row in rows]

    def get_records(self, user_name: str) -> list[sqlite3.Row]:
        with closing(self._connect()) as connection:
            return connection.execute(
                """
                SELECT weight_kg, height_m, bmi, category, recorded_at
                FROM bmi_records
                WHERE user_name = ? COLLATE NOCASE
                ORDER BY recorded_at ASC, id ASC
                """,
                (user_name,),
            ).fetchall()
