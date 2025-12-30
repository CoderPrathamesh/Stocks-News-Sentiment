"""
Enriched data writer - saves enriched events to daily CSV.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

from .data_manager import DataManager


class EnrichedWriter:
    """Writes enriched events to daily CSV files."""

    ENRICHED_FIELDS = [
        "symbol",
        "source",
        "published_at",
        "headline",
        "summary",
        "clean_text",
        "event_type",
        "is_routine",
        "is_potentially_negative",
        "impact_direction",
        "severity_score",
        "confidence_score",
        "flag_reason",
        "parser_version",
        "human_label",
        "human_comment",
        "raw_id",
    ]

    def __init__(self, data_manager: DataManager | None = None) -> None:
        self.data_manager = data_manager or DataManager()

    def write_enriched(
        self,
        records: List[Dict[str, Any]],
        target_date: date | None = None,
    ) -> int:
        """
        Write enriched records to daily CSV.

        Parameters
        ----------
        records : List[Dict[str, Any]]
            Enriched event records
        target_date : date | None
            Target date (default: today)

        Returns
        -------
        int
            Number of records written
        """
        if not records:
            return 0

        file_path = self.data_manager.get_enriched_file(target_date)
        file_exists = file_path.exists()

        # Ensure all records have required fields
        normalized_records: List[Dict[str, Any]] = []
        for record in records:
            normalized = {field: record.get(field, "") for field in self.ENRICHED_FIELDS}
            normalized_records.append(normalized)

        write_mode = "a" if file_exists else "w"
        with open(file_path, write_mode, encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.ENRICHED_FIELDS)
            if not file_exists:
                writer.writeheader()
            writer.writerows(normalized_records)

        return len(normalized_records)























