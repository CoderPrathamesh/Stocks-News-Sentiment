"""
Process logger - structured execution logging for daily pipeline runs.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict

from .data_manager import DataManager


class ProcessLogger:
    """Logs pipeline execution statistics to daily log files."""

    def __init__(self, data_manager: DataManager | None = None) -> None:
        self.data_manager = data_manager or DataManager()

    def log_run(
        self,
        stats: Dict[str, Any],
        target_date: date | None = None,
    ) -> None:
        """
        Log pipeline execution statistics.

        Parameters
        ----------
        stats : Dict[str, Any]
            Statistics dictionary with keys like:
            - raw_items_ingested
            - raw_items_new
            - enriched_items_created
            - routine_filtered
            - negative_flagged
            - signals_written
            - parser_version
            - model_version
            - execution_time_seconds
        target_date : date | None
            Target date (default: today)
        """
        log_file = self.data_manager.get_log_file(target_date)
        timestamp = datetime.now().isoformat()

        # Format log entry
        log_entry = f"[{timestamp}] PIPELINE_RUN\n"
        for key, value in stats.items():
            log_entry += f"  {key}: {value}\n"
        log_entry += "\n"

        # Append to log file
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)























