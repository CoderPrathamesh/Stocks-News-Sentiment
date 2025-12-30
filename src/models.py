from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class NewsItem:
    """Normalized representation of a single news / filing item."""

    ticker: str
    source: str
    headline: str
    body: str
    timestamp: datetime
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Event:
    """A classified negative (or neutral) event derived from a news item."""

    ticker: str
    source: str
    timestamp: datetime
    event_type: str  # e.g. "Guidance Cut / Profit Warning"
    is_routine: bool
    is_negative: bool
    base_severity: float  # 0–10, before pressure model
    credibility: float  # 0–1 based on source quality
    downside_risk: str  # "low" | "medium" | "high"
    justification: str
    raw_news: NewsItem


@dataclass
class EnrichedEvent:
    """Enriched event with full schema for ML-ready processing."""

    symbol: str
    source: str
    published_at: datetime
    event_date: datetime | None
    headline: str
    summary: str
    raw_text: str
    clean_text: str
    event_type: str  # Normalized from EVENT_TYPES taxonomy
    impact_direction: str  # NEGATIVE | POTENTIALLY_NEGATIVE | NEUTRAL | POTENTIALLY_POSITIVE | POSITIVE
    impact_confidence: float  # 0.0 - 1.0
    flag_reason: List[str]  # List of reason codes
    human_label: str | None = None  # For ML training feedback
    human_comment: str | None = None  # For ML training feedback
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Signal:
    """An actionable downside risk signal for a ticker."""

    ticker: str
    signal: str  # e.g. "DOWNSIDE_RISK"
    severity: float  # 0–10 downside pressure score
    confidence: str  # "Low" | "Medium" | "High"
    summary: str
    reasons: List[str]
    timestamp: datetime




