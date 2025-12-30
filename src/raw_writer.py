"""
Raw data writer - saves all incoming data exactly as received.

Never modifies raw data. Appends only new records.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Set

from .data_manager import DataManager


class RawWriter:
    """
    Writes raw announcements to daily CSV files.

    Ensures:
    - Raw data is never modified
    - Only new records are appended
    - Duplicate detection based on (symbol, source, published_at, headline)
    """

    def __init__(self, data_manager: DataManager | None = None) -> None:
        self.data_manager = data_manager or DataManager()
        self._seen_keys: Set[str] = set()

    def _make_key(self, record: Dict[str, Any]) -> str:
        """Create a unique key for duplicate detection."""
        symbol = str(record.get("symbol", ""))
        source = str(record.get("source", ""))
        published_at = str(record.get("published_at", ""))
        headline = str(record.get("headline", ""))[:100]  # Truncate for key
        return f"{symbol}|{source}|{published_at}|{headline}"

    def _load_existing_keys(self, file_path: Path) -> Set[str]:
        """Load existing record keys from file to avoid duplicates."""
        if not file_path.exists():
            return set()

        keys: Set[str] = set()
        try:
            with open(file_path, "r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames:
                    for row in reader:
                        key = self._make_key(row)
                        keys.add(key)
        except Exception:  # noqa: BLE001
            # If file is corrupted or empty, start fresh
            pass
        return keys

    def write_raw(
        self,
        records: List[Dict[str, Any]],
        target_date: date | None = None,
    ) -> int:
        """
        Write raw records to daily CSV, appending only new records.

        Parameters
        ----------
        records : List[Dict[str, Any]]
            Raw announcement records
        target_date : date | None
            Target date (default: today)

        Returns
        -------
        int
            Number of new records written
        """
        if not records:
            return 0

        file_path = self.data_manager.get_raw_file(target_date)
        file_exists = file_path.exists()

        # Load existing keys to avoid duplicates
        existing_keys = self._load_existing_keys(file_path) if file_exists else set()

        # Filter to only new records
        new_records: List[Dict[str, Any]] = []
        for record in records:
            key = self._make_key(record)
            if key not in existing_keys and key not in self._seen_keys:
                new_records.append(record)
                self._seen_keys.add(key)

        if not new_records:
            return 0

        # Determine fieldnames from first record
        fieldnames = list(new_records[0].keys())

        # Append to file
        write_mode = "a" if file_exists else "w"
        with open(file_path, write_mode, encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerows(new_records)

        return len(new_records)























