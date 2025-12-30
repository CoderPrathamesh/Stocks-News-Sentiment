"""
Human feedback storage for ML training.

This module allows storing human labels and comments on enriched events,
enabling supervised learning in the future.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import EnrichedEvent


class FeedbackStore:
    """
    Store human feedback on enriched events for ML training.
    """

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self._ensure_schema()

    def _get_conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _ensure_schema(self) -> None:
        """Create feedback table if it doesn't exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT,
                    event_type TEXT,
                    headline TEXT,
                    impact_direction TEXT,
                    impact_confidence REAL,
                    human_label TEXT,
                    human_comment TEXT,
                    flag_reason TEXT,
                    created_at TEXT,
                    event_data TEXT
                )
                """
            )
            conn.commit()

    def store_feedback(
        self,
        event: EnrichedEvent,
        human_label: str,
        human_comment: Optional[str] = None,
    ) -> None:
        """
        Store human feedback on an enriched event.

        Parameters
        ----------
        event : EnrichedEvent
            The enriched event being labeled
        human_label : str
            Human-provided label (e.g., "NEGATIVE", "NEUTRAL", "FALSE_POSITIVE")
        human_comment : str | None
            Optional comment explaining the label
        """
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO feedback (
                    symbol, event_type, headline, impact_direction,
                    impact_confidence, human_label, human_comment,
                    flag_reason, created_at, event_data
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.symbol,
                    event.event_type,
                    event.headline,
                    event.impact_direction,
                    event.impact_confidence,
                    human_label,
                    human_comment,
                    json.dumps(event.flag_reason),
                    datetime.utcnow().isoformat(),
                    json.dumps(event.raw),
                ),
            )
            conn.commit()

    def get_feedback_history(
        self,
        symbol: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve feedback history.

        Parameters
        ----------
        symbol : str | None
            Filter by symbol (optional)
        limit : int
            Maximum number of records to return

        Returns
        -------
        List[Dict[str, Any]]
            List of feedback records
        """
        with self._get_conn() as conn:
            if symbol:
                cursor = conn.execute(
                    """
                    SELECT * FROM feedback
                    WHERE symbol = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (symbol, limit),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT * FROM feedback
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                )

            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]























