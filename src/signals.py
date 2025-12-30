from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Iterable, List

from .models import Event, Signal


class SignalGenerator:
    """
    Turn rolling pressure scores + recent events into actionable downside signals.
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
        events: Iterable[Event],
        scores: Dict[str, float],
        now: datetime | None = None,
    ) -> List[Signal]:
        now = now or datetime.utcnow()
        per_ticker_events: Dict[str, List[Event]] = {}

        for ev in events:
            if not ev.is_negative:
                continue
            if now - ev.timestamp > self.recency:
                continue
            per_ticker_events.setdefault(ev.ticker, []).append(ev)

        signals: List[Signal] = []
        for ticker, ticker_events in per_ticker_events.items():
            score = scores.get(ticker, 0.0)
            if score < self.min_score:
                continue

            reasons = [
                f"{ev.event_type} ({ev.downside_risk}) from {ev.source} on {ev.timestamp.date()}"
                for ev in ticker_events
            ]
            summary = (
                f"Accumulated negative events over last {self.recency.days} days "
                f"for {ticker}: {len(ticker_events)} material items."
            )

            if score >= 8.0:
                confidence = "High"
            elif score >= 6.0:
                confidence = "Medium"
            else:
                confidence = "Low"

            signals.append(
                Signal(
                    ticker=ticker,
                    signal="DOWNSIDE_RISK",
                    severity=score,
                    confidence=confidence,
                    summary=summary,
                    reasons=reasons,
                    timestamp=now,
                )
            )

        return signals


