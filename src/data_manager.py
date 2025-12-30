"""
Data directory manager for daily raw/enriched/signals/logs organization.

Ensures all paths exist and handles date-based folder creation.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path


class DataManager:
    """
    Manages daily data directories for raw, enriched, signals, and logs.

    Structure:
    - data/raw/YYYY-MM-DD/raw_announcements.csv
    - data/enriched/YYYY-MM-DD/enriched_events.csv
    - data/signals/YYYY-MM-DD/negative_signals.csv
    - logs/YYYY-MM-DD/pipeline.log
    """

    def __init__(self, base_dir: str | Path = ".") -> None:
        self.base_dir = Path(base_dir)
        self.data_dir = self.base_dir / "data"
        self.logs_dir = self.base_dir / "logs"

    def get_raw_dir(self, target_date: date | None = None) -> Path:
        """Get directory for raw data for a given date (default: today)."""
        if target_date is None:
            target_date = date.today()
        raw_dir = self.data_dir / "raw" / target_date.isoformat()
        raw_dir.mkdir(parents=True, exist_ok=True)
        return raw_dir

    def get_enriched_dir(self, target_date: date | None = None) -> Path:
        """Get directory for enriched data for a given date (default: today)."""
        if target_date is None:
            target_date = date.today()
        enriched_dir = self.data_dir / "enriched" / target_date.isoformat()
        enriched_dir.mkdir(parents=True, exist_ok=True)
        return enriched_dir

    def get_signals_dir(self, target_date: date | None = None) -> Path:
        """Get directory for signals for a given date (default: today)."""
        if target_date is None:
            target_date = date.today()
        signals_dir = self.data_dir / "signals" / target_date.isoformat()
        signals_dir.mkdir(parents=True, exist_ok=True)
        return signals_dir

    def get_logs_dir(self, target_date: date | None = None) -> Path:
        """Get directory for logs for a given date (default: today)."""
        if target_date is None:
            target_date = date.today()
        logs_dir = self.logs_dir / target_date.isoformat()
        logs_dir.mkdir(parents=True, exist_ok=True)
        return logs_dir

    def get_raw_file(self, target_date: date | None = None) -> Path:
        """Get path to raw_announcements.csv for a given date."""
        return self.get_raw_dir(target_date) / "raw_announcements.csv"

    def get_enriched_file(self, target_date: date | None = None) -> Path:
        """Get path to enriched_events.csv for a given date."""
        return self.get_enriched_dir(target_date) / "enriched_events.csv"

    def get_signals_file(self, target_date: date | None = None) -> Path:
        """Get path to negative_signals.csv for a given date."""
        return self.get_signals_dir(target_date) / "negative_signals.csv"

    def get_log_file(self, target_date: date | None = None) -> Path:
        """Get path to pipeline.log for a given date."""
        return self.get_logs_dir(target_date) / "pipeline.log"























