"""
Enrichment layer v3 - transforms raw data into enriched schema.

This is the deterministic enrichment layer before any ML.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict

from .event_normalizer import normalize_event_type
from .models import NewsItem


def clean_text(text: str) -> str:
    """Clean and normalize text."""
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    text = re.sub(r"\ufeff", "", text)
    return text


def enrich_record(
    raw_record: Dict[str, Any],
    parser_version: str = "v3.0",
) -> Dict[str, Any]:
    """
    Enrich a raw record into the full schema.

    Parameters
    ----------
    raw_record : Dict[str, Any]
        Raw announcement record
    parser_version : str
        Version of the parser/enrichment logic

    Returns
    -------
    Dict[str, Any]
        Enriched record with all required fields
    """
    symbol = str(raw_record.get("symbol", ""))
    source = str(raw_record.get("source", ""))
    published_at = str(raw_record.get("published_at", ""))
    headline = str(raw_record.get("headline", ""))
    summary = str(raw_record.get("summary", "") or raw_record.get("body", ""))
    
    # Extract attachment filename from raw data for fraud detection
    # Attachment filenames often contain important keywords (e.g., "Fraud" in filename)
    attachment_text = ""
    if "raw" in raw_record:
        raw_data = raw_record.get("raw", {})
        if isinstance(raw_data, dict):
            attchmnt_file = str(raw_data.get("attchmntFile", "") or "")
            if attchmnt_file and attchmnt_file != "-":
                # Extract filename from URL or path
                attachment_text = " " + attchmnt_file.lower()

    # Clean text (include attachment filename for better fraud detection)
    clean_text_val = clean_text(headline + " " + summary + attachment_text)

    # Extract NSE category (check multiple possible fields)
    nse_category = (
        str(raw_record.get("nse_category", ""))
        or str(raw_record.get("category", ""))
        or ""
    )
    # Also check raw dict if available
    if not nse_category and "raw" in raw_record:
        raw_data = raw_record.get("raw", {})
        if isinstance(raw_data, dict):
            nse_category = (
                str(raw_data.get("category", ""))
                or str(raw_data.get("subCategoryName", ""))
                or str(raw_data.get("sub_category", ""))
                or str(raw_data.get("announcementCategory", ""))
                or ""
            )

    # Normalize event type
    event_type = normalize_event_type(nse_category, headline, summary)

    # Determine routine status and impact (will be refined by classifier)
    # For now, set defaults
    is_routine = False
    is_potentially_negative = False
    impact_direction = "NEUTRAL"
    severity_score = 0.0
    confidence_score = 0.5
    flag_reason: list[str] = []

    # Build enriched record
    enriched = {
        "symbol": symbol,
        "source": source,
        "published_at": published_at,
        "headline": headline,
        "summary": summary,
        "clean_text": clean_text_val,
        "event_type": event_type,
        "is_routine": is_routine,
        "is_potentially_negative": is_potentially_negative,
        "impact_direction": impact_direction,
        "severity_score": severity_score,
        "confidence_score": confidence_score,
        "flag_reason": ",".join(flag_reason) if flag_reason else "",
        "parser_version": parser_version,
        "human_label": "",  # Empty by default, filled manually later
        "human_comment": "",  # Empty by default, filled manually later
        # Preserve raw data reference and raw dict for attachment filename extraction
        "raw_id": str(raw_record.get("id", "")),
        "raw": raw_record.get("raw", {}),  # Preserve raw dict for classifier access
    }

    return enriched

