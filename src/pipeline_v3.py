"""
Pipeline v3 - Separated ingestion, enrichment, filtering, and logging.

Architecture:
1. Raw ingestion (never modify)
2. Enrichment layer
3. Routine filtering
4. Negative risk classification
5. Signal generation
6. Daily file organization
"""

from __future__ import annotations

import time
from datetime import date, datetime
from typing import Any, Dict, List

from .data_manager import DataManager
from .enriched_writer import EnrichedWriter
from .enrichment_v3 import enrich_record
from .negative_classifier_v3 import classify_negative_risk
from .process_logger import ProcessLogger
from .raw_writer import RawWriter
from .routine_filter_v3 import apply_routine_filter
from .signals_writer import SignalsWriter


def run_pipeline_v3(
    raw_articles: List[Dict[str, Any]],
    parser_version: str = "v3.0",
    target_date: date | None = None,
) -> Dict[str, Any]:
    """
    Run the complete v3 pipeline: raw → enriched → filtered → signals.

    Parameters
    ----------
    raw_articles : List[Dict[str, Any]]
        Raw announcement articles from collectors
    parser_version : str
        Version of parser/enrichment logic
    target_date : date | None
        Target date for file organization (default: today)

    Returns
    -------
    Dict[str, Any]
        Execution statistics
    """
    start_time = time.time()
    target_date = target_date or date.today()

    # Initialize components
    data_manager = DataManager()
    raw_writer = RawWriter(data_manager)
    enriched_writer = EnrichedWriter(data_manager)
    signals_writer = SignalsWriter(data_manager)
    logger = ProcessLogger(data_manager)

    stats = {
        "raw_items_ingested": len(raw_articles),
        "raw_items_new": 0,
        "enriched_items_created": 0,
        "routine_filtered": 0,
        "negative_flagged": 0,
        "signals_written": 0,
        "parser_version": parser_version,
        "model_version": "deterministic_v3",
        "target_date": target_date.isoformat(),
    }

    if not raw_articles:
        stats["execution_time_seconds"] = time.time() - start_time
        logger.log_run(stats, target_date)
        return stats

    # Step 1: Write raw data (never modify)
    try:
        raw_count = raw_writer.write_raw(raw_articles, target_date)
        stats["raw_items_new"] = raw_count
    except Exception as e:  # noqa: BLE001
        stats["raw_write_error"] = str(e)
        # Continue even if raw write fails (but log it)

    # Step 2: Enrich all records
    enriched_records: List[Dict[str, Any]] = []
    for raw_article in raw_articles:
        try:
            enriched = enrich_record(raw_article, parser_version=parser_version)
            enriched_records.append(enriched)
        except Exception as e:  # noqa: BLE001
            # Skip records that fail enrichment, but continue
            continue

    stats["enriched_items_created"] = len(enriched_records)

    # Step 3: Apply routine filter
    filtered_records: List[Dict[str, Any]] = []
    for enriched in enriched_records:
        filtered = apply_routine_filter(enriched.copy())
        if filtered.get("is_routine", False):
            stats["routine_filtered"] += 1
        filtered_records.append(filtered)

    # Step 4: Apply negative risk classification
    classified_records: List[Dict[str, Any]] = []
    for filtered in filtered_records:
        classified = classify_negative_risk(filtered.copy())
        if classified.get("is_potentially_negative", False):
            stats["negative_flagged"] += 1
        classified_records.append(classified)

    # Step 5: Write enriched data
    try:
        enriched_writer.write_enriched(classified_records, target_date)
    except Exception as e:  # noqa: BLE001
        stats["enriched_write_error"] = str(e)

    # Step 6: Write signals (only negative/watch)
    try:
        signals_count = signals_writer.write_signals(classified_records, target_date)
        stats["signals_written"] = signals_count
    except Exception as e:  # noqa: BLE001
        stats["signals_write_error"] = str(e)

    # Step 7: Log execution
    stats["execution_time_seconds"] = round(time.time() - start_time, 2)
    logger.log_run(stats, target_date)

    return stats























