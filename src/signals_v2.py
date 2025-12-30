"""
Signal generator for EnrichedEvent.

Produces ranked downside risk signals.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Iterable, List

from .models import EnrichedEvent


@dataclass
class EnrichedSignal:
    """Extended signal with enrichment fields for ranked output."""

    ticker: str
    signal: str
    severity: float
    confidence: str
    summary: str
    reasons: List[str]
    timestamp: datetime
    event_type: str
    impact_direction: str
    impact_confidence: float
    flag_reason: List[str]
    headline: str


class SignalGeneratorV2:
    """
    Generate ranked downside risk signals from enriched events.
    """

    def __init__(
        self,
        min_score: float = 4.5,
        recency_days: int = 10,
    ) -> None:
        self.min_score = min_score
        self.recency = timedelta(days=recency_days)

    def generate(
        self,
        events: Iterable[EnrichedEvent],
        scores: Dict[str, float],
        now: datetime | None = None,
    ) -> List[EnrichedSignal]:
        """
        Generate ranked signals from enriched events and pressure scores.

        Returns signals sorted by severity (highest first).
        """
        now = now or datetime.utcnow()
        per_ticker_events: Dict[str, List[EnrichedEvent]] = {}

        for ev in events:
            if ev.impact_direction not in ["NEGATIVE", "POTENTIALLY_NEGATIVE"]:
                continue
            if now - ev.published_at > self.recency:
                continue
            per_ticker_events.setdefault(ev.symbol, []).append(ev)

        signals: List[EnrichedSignal] = []
        for ticker, ticker_events in per_ticker_events.items():
            score = scores.get(ticker, 0.0)
            if score < self.min_score:
                continue

            # Get the most recent/important event for headline and metadata
            most_recent = max(ticker_events, key=lambda e: e.published_at)
            headline = most_recent.headline[:100]  # Truncate if needed

            reasons = [
                f"{ev.event_type} ({ev.impact_direction}, conf={ev.impact_confidence:.2f}) "
                f"from {ev.source} on {ev.published_at.date()}"
                for ev in ticker_events
            ]
            summary = (
                f"Accumulated {len(ticker_events)} negative event(s) over last {self.recency.days} days. "
                f"Event types: {', '.join(set(e.event_type for e in ticker_events))}"
            )

            if score >= 8.0:
                confidence_str = "High"
            elif score >= 6.0:
                confidence_str = "Medium"
            else:
                confidence_str = "Low"

            # Aggregate flag reasons from all events
            all_flag_reasons = []
            for ev in ticker_events:
                all_flag_reasons.extend(ev.flag_reason)
            unique_flag_reasons = list(set(all_flag_reasons))

            signals.append(
                EnrichedSignal(
                    ticker=ticker,
                    signal="DOWNSIDE_RISK",
                    severity=score,
                    confidence=confidence_str,
                    summary=summary,
                    reasons=reasons,
                    timestamp=now,
                    event_type=most_recent.event_type,
                    impact_direction=most_recent.impact_direction,
                    impact_confidence=most_recent.impact_confidence,
                    flag_reason=unique_flag_reasons,
                    headline=headline,
                )
            )

        # Sort by severity (highest first)
        signals.sort(key=lambda s: s.severity, reverse=True)
        return signals

