"""SQLite job log. Production can swap this for Postgres SKIP LOCKED."""

import json
import sqlite3
import threading
from pathlib import Path

from neo_personal_bot.tickets import Card


class Store:
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        self._init()

    def _init(self) -> None:
        with self._lock:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind TEXT NOT NULL,
                    status TEXT NOT NULL,
                    request_text TEXT NOT NULL,
                    card_json TEXT NOT NULL
                )
                """
            )
            self._conn.commit()

    def add(self, request_text: str, card: Card) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO jobs (kind, status, request_text, card_json) VALUES (?, ?, ?, ?)",
                (card.kind, card.status, request_text, card.model_dump_json()),
            )
            self._conn.commit()

    def list_jobs(self) -> list[dict[str, object]]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT id, kind, status, request_text, card_json FROM jobs ORDER BY id DESC"
            ).fetchall()
        jobs: list[dict[str, object]] = []
        for row in rows:
            card = json.loads(row["card_json"])
            jobs.append(
                {
                    "id": row["id"],
                    "kind": row["kind"],
                    "status": row["status"],
                    "request_text": row["request_text"],
                    "card": card,
                }
            )
        return jobs

    def close(self) -> None:
        self._conn.close()
