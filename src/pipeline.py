"""
Full downside-risk pipeline from raw articles → actionable signals.

Layers:
1) News ingestion / normalization
2) Rule-based routine filter
3) Event classification
4) Optional context interpreter (LLM hook)
5) Rolling negative pressure model (7–14 days)
6) Signal generation with strict thresholds
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from .classifier import classify_news
from .context import enrich_with_context
from .filters import filter_routine
from .models import Event, NewsItem, Signal
from .pressure import RollingNegativePressure
from .signals import SignalGenerator


def _to_news_items(raw_articles: List[Dict[str, Any]]) -> List[NewsItem]:
    items: List[NewsItem] = []

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
    return items


def run_pipeline(
    articles: List[Dict[str, Any]],
    context_enabled: bool = False,
) -> List[Dict[str, Any]]:
    """
    Full pipeline from raw ingested articles → downside risk signals (dict form).
    """
    if not articles:
        return []

    news_items = _to_news_items(articles)

    # 1) Routine filter (FIRST GATE)
    filtered_news = filter_routine(news_items)

    # 2) Event classification
    events: List[Event] = []
    for n in filtered_news:
        ev = classify_news(n)
        if ev is None:
            continue
        if context_enabled:
            ev = enrich_with_context(ev)
        if not ev.is_negative:
            continue
        events.append(ev)

    if not events:
        return []

    # 3) Rolling pressure (7–14 days)
    rpm = RollingNegativePressure(window_days=14, half_life_days=7)
    scores = rpm.compute_scores(events)

    # 4) Signal generation
    gen = SignalGenerator(min_score=5.0, recency_days=7)
    sigs: List[Signal] = gen.generate(events, scores)

    out: List[Dict[str, Any]] = []
    for s in sigs:
        out.append(
            {
                "symbol": s.ticker,
                "source": "NEGATIVE_PIPELINE",
                "headline": f"Downside risk signal ({s.severity:.1f}/10)",
                "summary": s.summary,
                "published_at": s.timestamp.isoformat(),
                "score": s.severity,
                "raw": {
                    "signal": s.signal,
                    "confidence": s.confidence,
                    "reasons": s.reasons,
                },
            }
        )

    return out




