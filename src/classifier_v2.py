"""
Refactored classifier using enrichment + impact interpretation.

This replaces the old keyword-only classifier with:
- Event normalization
- Context-aware impact interpretation
- Explainable flag reasons
"""

from __future__ import annotations

from typing import List

from .enrichment import enrich_news_item
from .impact_interpreter import apply_impact_interpretation
from .models import EnrichedEvent, NewsItem


def classify_and_enrich(
    news: NewsItem,
    nse_category: str = "",
    context_enabled: bool = False,
) -> EnrichedEvent | None:
    """
    Classify and enrich a news item into an EnrichedEvent.

    This is the main entry point for the new enrichment-based pipeline.

    Parameters
    ----------
    news : NewsItem
        Raw news item
    nse_category : str
        NSE category string (from raw data, e.g., "General Updates", "Action(s) taken or orders passed")
    context_enabled : bool
        Whether to use context-aware interpretation (future ML hook)

    Returns
    -------
    EnrichedEvent | None
        Enriched event, or None if routine/neutral and should be filtered
    """
    # Step 1: Enrich the news item
    enriched = enrich_news_item(news, nse_category=nse_category, context_enabled=context_enabled)

    # Step 2: Apply impact interpretation
    enriched = apply_impact_interpretation(enriched)

    # Step 3: Filter routine/neutral events (only return NEGATIVE or POTENTIALLY_NEGATIVE)
    if enriched.impact_direction in ["NEGATIVE", "POTENTIALLY_NEGATIVE"]:
        return enriched

    # For now, we filter out NEUTRAL, POTENTIALLY_POSITIVE, POSITIVE
    # (can be adjusted based on requirements)
    return None


def batch_classify_and_enrich(
    news_items: List[NewsItem],
    nse_categories: List[str] | None = None,
    context_enabled: bool = False,
) -> List[EnrichedEvent]:
    """
    Batch classify and enrich multiple news items.

    Parameters
    ----------
    news_items : List[NewsItem]
        List of raw news items
    nse_categories : List[str] | None
        Optional list of NSE categories (one per news item)
    context_enabled : bool
        Whether to use context-aware interpretation

    Returns
    -------
    List[EnrichedEvent]
        List of enriched events (only NEGATIVE or POTENTIALLY_NEGATIVE)
    """
    if nse_categories is None:
        nse_categories = [""] * len(news_items)

    enriched_events: List[EnrichedEvent] = []
    for news, category in zip(news_items, nse_categories):
        enriched = classify_and_enrich(news, nse_category=category, context_enabled=context_enabled)
        if enriched is not None:
            enriched_events.append(enriched)

    return enriched_events























