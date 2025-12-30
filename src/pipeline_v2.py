"""
Refactored pipeline using enrichment layer + impact interpretation.

This is the new pipeline that:
1. Ingests raw articles
2. Enriches with full schema
3. Applies impact interpretation
4. Filters to only NEGATIVE/POTENTIALLY_NEGATIVE
5. Computes rolling pressure
6. Generates ranked signals
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from .classifier_v2 import batch_classify_and_enrich
from .models import EnrichedEvent, NewsItem
from .pressure_v2 import RollingNegativePressureV2
from .signals_v2 import EnrichedSignal, SignalGeneratorV2


def _to_news_items(raw_articles: List[Dict[str, Any]]) -> tuple[List[NewsItem], List[str]]:
    """
    Convert raw article dicts to NewsItems and extract NSE categories.

    Returns
    -------
    tuple[List[NewsItem], List[str]]
        (news_items, nse_categories)
    """
    items: List[NewsItem] = []
    categories: List[str] = []

    for a in raw_articles:
        ts_raw = a.get("published_at") or a.get("datetime")
        if isinstance(ts_raw, str):
            try:
                ts = datetime.fromisoformat(ts_raw)
            except Exception:  # noqa: BLE001
                ts = datetime.utcnow()
        elif isinstance(ts_raw, datetime):
            ts = ts_raw
        else:
            ts = datetime.utcnow()

        # Extract NSE category from raw data
        nse_category = a.get("nse_category", "") or a.get("category", "") or ""
        # Also check raw dict for category
        if not nse_category and "raw" in a:
            raw_data = a.get("raw", {})
            nse_category = (
                raw_data.get("category")
                or raw_data.get("subCategoryName")
                or raw_data.get("sub_category")
                or raw_data.get("announcementCategory")
                or ""
            )

        items.append(
            NewsItem(
                ticker=a.get("symbol") or a.get("ticker") or "",
                source=a.get("source", "unknown"),
                headline=a.get("headline", ""),
                body=a.get("body", "") or a.get("summary", ""),
                timestamp=ts,
                raw=a,
            )
        )
        categories.append(nse_category)

    return items, categories


def run_pipeline_v2(
    articles: List[Dict[str, Any]],
    context_enabled: bool = False,
) -> List[Dict[str, Any]]:
    """
    New pipeline using enrichment + impact interpretation.

    Returns only NEGATIVE and POTENTIALLY_NEGATIVE events, ranked by severity.

    Parameters
    ----------
    articles : List[Dict[str, Any]]
        Raw articles from collectors
    context_enabled : bool
        Whether to use context-aware interpretation

    Returns
    -------
    List[Dict[str, Any]]
        Ranked list of downside risk signals (dict format for storage)
    """
    if not articles:
        return []

    # Step 1: Convert to NewsItems + extract NSE categories
    news_items, nse_categories = _to_news_items(articles)

    # Step 2: Classify and enrich (filters routine/neutral automatically)
    enriched_events = batch_classify_and_enrich(
        news_items, nse_categories=nse_categories, context_enabled=context_enabled
    )

    if not enriched_events:
        return []

    # Step 3: Compute rolling negative pressure
    rpm = RollingNegativePressureV2(window_days=14, half_life_days=7)
    scores = rpm.compute_scores(enriched_events)

    # Step 4: Generate signals
    gen = SignalGeneratorV2(min_score=4.5, recency_days=10)
    signals = gen.generate(enriched_events, scores)

    # Step 5: Convert to dict format for storage/display
    out: List[Dict[str, Any]] = []
    for sig in signals:
        out.append(
            {
                "symbol": sig.ticker,
                "source": "NEGATIVE_PIPELINE_V2",
                "headline": sig.headline,
                "summary": sig.summary,
                "published_at": sig.timestamp.isoformat(),
                "score": sig.severity,
                "event_type": sig.event_type,
                "impact_direction": sig.impact_direction,
                "impact_confidence": sig.impact_confidence,
                "flag_reason": sig.flag_reason,
                "raw": {
                    "signal": sig.signal,
                    "confidence": sig.confidence,
                    "reasons": sig.reasons,
                },
            }
        )

    return out

