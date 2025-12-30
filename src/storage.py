"""
Simple SQLite-based storage for signals.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, List


class SignalStore:
    """
    Store signals in a local SQLite database.
    """

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self._ensure_schema()

    def _get_conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _ensure_schema(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT,
                    source TEXT,
                    headline TEXT,
                    summary TEXT,
                    published_at TEXT,
                    score REAL,
                    raw_json TEXT
                )
                """
            )
            conn.commit()

    def insert_signals(self, signals: Iterable[Dict[str, Any]]) -> None:
        rows: List[tuple[Any, ...]] = []
        for s in signals:
            rows.append(
                (
                    s.get("symbol"),
                    s.get("source"),
                    s.get("headline"),
                    s.get("summary"),
                    s.get("published_at"),
                    s.get("score"),
                    json.dumps(s.get("raw", s)),
                )
            )

        if not rows:
            return

        with self._get_conn() as conn:
            conn.executemany(
                """
                INSERT INTO signals (
                    symbol, source, headline, summary,
                    published_at, score, raw_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
            conn.commit()



























