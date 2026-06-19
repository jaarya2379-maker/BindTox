from __future__ import annotations

import os
import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path

from .schemas import AlertRecord


class AlertRepository(ABC):
    @abstractmethod
    def save_alert(self, alert: AlertRecord) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_alerts(self, limit: int = 10) -> list[AlertRecord]:
        raise NotImplementedError


class InMemoryAlertRepository(AlertRepository):
    def __init__(self) -> None:
        self._alerts: list[AlertRecord] = []

    def save_alert(self, alert: AlertRecord) -> None:
        self._alerts.insert(0, alert)

    def list_alerts(self, limit: int = 10) -> list[AlertRecord]:
        return self._alerts[:limit]


class MongoAlertRepository(AlertRepository):
    def __init__(self, uri: str, database: str = "breachwatch", collection: str = "alerts") -> None:
        from pymongo import MongoClient

        self._client = MongoClient(uri)
        self._collection = self._client[database][collection]

    def save_alert(self, alert: AlertRecord) -> None:
        self._collection.insert_one(alert.model_dump(mode="json"))

    def list_alerts(self, limit: int = 10) -> list[AlertRecord]:
        cursor = self._collection.find().sort("created_at", -1).limit(limit)
        return [AlertRecord.model_validate(item) for item in cursor]


class SQLiteAlertRepository(AlertRepository):
    def __init__(self, path: str | Path = "artifacts/breachwatch_alerts.sqlite3") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    risk_score INTEGER NOT NULL,
                    breach_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def save_alert(self, alert: AlertRecord) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO alerts (email, risk_score, breach_count, created_at, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    alert.email,
                    alert.risk_score,
                    alert.breach_count,
                    alert.created_at.isoformat(),
                    alert.status,
                ),
            )
            connection.commit()

    def list_alerts(self, limit: int = 10) -> list[AlertRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT email, risk_score, breach_count, created_at, status
                FROM alerts
                ORDER BY datetime(created_at) DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            AlertRecord(
                email=row[0],
                risk_score=row[1],
                breach_count=row[2],
                created_at=row[3],
                status=row[4],
            )
            for row in rows
        ]


def build_alert_repository() -> AlertRepository:
    repository_mode = os.getenv("BREACHWATCH_DB_MODE", "sqlite").strip().lower()
    if repository_mode == "mongo":
        mongo_uri = os.getenv("BREACHWATCH_MONGO_URI")
        if not mongo_uri:
            return InMemoryAlertRepository()
        try:
            return MongoAlertRepository(uri=mongo_uri)
        except Exception:
            return InMemoryAlertRepository()
    if repository_mode == "memory":
        return InMemoryAlertRepository()
    sqlite_path = os.getenv("BREACHWATCH_SQLITE_PATH", "artifacts/breachwatch_alerts.sqlite3")
    return SQLiteAlertRepository(path=sqlite_path)
