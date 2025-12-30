"""
Data enrichment layer: Transform raw filings into enriched schema.

This module handles:
- Text cleaning and normalization
- Event type normalization
- Impact direction and confidence assignment
- Flag reason generation
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from .event_normalizer import normalize_event_type
from .models import EnrichedEvent, NewsItem


def clean_text(text: str) -> str:
    """
    Clean and normalize text for processing.

    - Remove extra whitespace
    - Normalize case (preserve sentence structure)
    - Remove special formatting artifacts
    """
    if not text:
        return ""

    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text)
    # Remove leading/trailing whitespace
    text = text.strip()
    # Remove common artifacts
    text = re.sub(r"\ufeff", "", text)  # BOM
    text = re.sub(r"\r\n", " ", text)  # Windows line breaks
    text = re.sub(r"\n+", " ", text)  # Multiple newlines

    return text


def extract_event_date(headline: str, summary: str, published_at: Optional[datetime]) -> Optional[datetime]:
    """
    Try to extract the actual event date from text, fallback to published_at.
    """
    # For now, use published_at. Can be enhanced with date parsing from text.
    return published_at


def generate_flag_reasons(
    event_type: str,
    headline: str,
    summary: str,
    nse_category: str,
) -> List[str]:
    """
    Generate explainable flag reasons for why an event was flagged.

    Returns a list of reason codes that explain the classification.
    """
    reasons: List[str] = []
    text = (headline + " " + summary).lower()
    cat_lower = nse_category.lower()

    # REGULATOR_MENTION
    regulator_keywords = ["rbi", "sebi", "fda", "dgca", "irda", "mca", "sfio", "cbi"]
    if any(reg in text for reg in regulator_keywords):
        reasons.append("REGULATOR_MENTION")

    # LEGAL_LANGUAGE
    legal_keywords = [
        "litigation",
        "dispute",
        "order passed",
        "demand notice",
        "show cause",
        "fir",
        "probe",
        "investigation",
        "summons",
    ]
    if any(kw in text for kw in legal_keywords):
        reasons.append("LEGAL_LANGUAGE")

    # KEY_PHRASE_DETECTED
    if event_type in ["REGULATORY_ACTION", "LITIGATION", "FINANCIAL_STRESS"]:
        reasons.append("KEY_PHRASE_DETECTED")

    # EXCHANGE_CLARIFICATION
    if "news verification" in cat_lower or "rumour verification" in cat_lower:
        reasons.append("EXCHANGE_CLARIFICATION")

    # SIMILAR_PAST_NEGATIVE_EVENT (placeholder for future ML similarity matching)
    # For now, we don't have historical data, so skip this

    # If no specific reasons, add generic
    if not reasons:
        reasons.append("EVENT_TYPE_MATCHED")

    return reasons


def enrich_news_item(
    news: NewsItem,
    nse_category: str = "",
    context_enabled: bool = False,
) -> EnrichedEvent:
    """
    Enrich a raw NewsItem into an EnrichedEvent with full schema.

    Parameters
    ----------
    news : NewsItem
        Raw news item from collector
    nse_category : str
        NSE category string (from raw data)
    context_enabled : bool
        Whether to use context-aware interpretation (future ML hook)

    Returns
    -------
    EnrichedEvent
        Fully enriched event with all fields populated
    """
    # Combine headline + body for processing
    raw_text = (news.headline + " " + news.body).strip()
    clean_text_val = clean_text(raw_text)

    # Normalize event type
    event_type = normalize_event_type(nse_category, news.headline, news.body)

    # Extract event date (for now, use published_at)
    event_date = extract_event_date(news.headline, news.body, news.timestamp)

    # Generate flag reasons
    flag_reasons = generate_flag_reasons(event_type, news.headline, news.body, nse_category)

    # Impact direction and confidence will be set by impact_interpreter
    # For now, set defaults (will be overridden)
    impact_direction = "NEUTRAL"
    impact_confidence = 0.5

    return EnrichedEvent(
        symbol=news.ticker,
        source=news.source,
        published_at=news.timestamp,
        event_date=event_date,
        headline=news.headline,
        summary=news.body,
        raw_text=raw_text,
        clean_text=clean_text_val,
        event_type=event_type,
        impact_direction=impact_direction,
        impact_confidence=impact_confidence,
        flag_reason=flag_reasons,
        human_label=None,
        human_comment=None,
        raw=news.raw,
    )

