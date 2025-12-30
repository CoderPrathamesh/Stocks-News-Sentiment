"""
Signals writer - saves negative/watch signals to daily CSV for human review.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

from .data_manager import DataManager


class SignalsWriter:
    """Writes negative/watch signals to daily CSV for human review."""

    SIGNAL_FIELDS = [
        "symbol",
        "event_type",
        "impact_direction",
        "severity_score",
        "confidence_score",
        "headline",
        "flag_reason",
        "source",
        "published_at",
    ]

    def __init__(self, data_manager: DataManager | None = None) -> None:
        self.data_manager = data_manager or DataManager()

    def write_signals(
        self,
        enriched_records: List[Dict[str, Any]],
        target_date: date | None = None,
    ) -> int:
        """
        Write negative/watch signals to daily CSV.

        Only writes records where:
        - is_potentially_negative = True
        - impact_direction in [NEGATIVE, WATCH]

        Parameters
        ----------
        enriched_records : List[Dict[str, Any]]
            Enriched event records
        target_date : date | None
            Target date (default: today)

        Returns
        -------
        int
            Number of signals written
        """
        # Filter to only negative/watch signals
        signals: List[Dict[str, Any]] = []
        for record in enriched_records:
            if not record.get("is_potentially_negative", False):
                continue
            impact = str(record.get("impact_direction", "")).upper()
            if impact not in ["NEGATIVE", "WATCH"]:
                continue

            signal = {
                "symbol": record.get("symbol", ""),
                "event_type": record.get("event_type", ""),
                "impact_direction": impact,
                "severity_score": record.get("severity_score", 0.0),
                "confidence_score": record.get("confidence_score", 0.0),
                "headline": record.get("headline", ""),
                "flag_reason": record.get("flag_reason", ""),
                "source": record.get("source", ""),
                "published_at": record.get("published_at", ""),
            }
            signals.append(signal)

        if not signals:
            return 0

        file_path = self.data_manager.get_signals_file(target_date)
        file_exists = file_path.exists()

        write_mode = "a" if file_exists else "w"
        with open(file_path, write_mode, encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.SIGNAL_FIELDS)
            if not file_exists:
                writer.writeheader()
            writer.writerows(signals)

        return len(signals)























