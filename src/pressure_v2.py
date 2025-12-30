"""
Rolling negative pressure model for EnrichedEvent.

Works with the new enrichment schema.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from math import exp
from typing import Dict, Iterable, List, Set, Tuple

from .models import EnrichedEvent


class RollingNegativePressureV2:
    """
    Rolling 7–14 day negative pressure model for each ticker.

    Uses EnrichedEvent with impact_direction and impact_confidence.
    """

    def __init__(self, window_days: int = 14, half_life_days: int = 7) -> None:
        self.window = timedelta(days=window_days)
        self.half_life = half_life_days

    def _decay_weight(self, age_days: float) -> float:
        # exponential decay: weight = 0.5 ** (age_days / half_life)
        return 0.5 ** (age_days / self.half_life)

    def _event_severity(self, event: EnrichedEvent) -> float:
        """
        Convert EnrichedEvent to a severity score (0-10).

        Uses impact_direction and impact_confidence.
        """
        base_scores = {
            "NEGATIVE": 8.0,
            "POTENTIALLY_NEGATIVE": 5.0,
            "NEUTRAL": 0.0,
            "POTENTIALLY_POSITIVE": 0.0,
            "POSITIVE": 0.0,
        }
        base = base_scores.get(event.impact_direction, 0.0)
        # Scale by confidence
        return base * event.impact_confidence

    def compute_scores(
        self,
        events: Iterable[EnrichedEvent],
        now: datetime | None = None,
    ) -> Dict[str, float]:
        """
        Return downside pressure scores in [0, 10] per ticker.
        """
        now = now or datetime.utcnow()

        per_ticker_events: Dict[str, List[Tuple[EnrichedEvent, float]]] = defaultdict(list)

        for ev in events:
            # Only process NEGATIVE or POTENTIALLY_NEGATIVE
            if ev.impact_direction not in ["NEGATIVE", "POTENTIALLY_NEGATIVE"]:
                continue

            age_td = now - ev.published_at
            age = age_td.days + age_td.seconds / 86400.0
            if age > self.window.days:
                continue

            w = self._decay_weight(age)
            severity = self._event_severity(ev)
            eff_sev = severity * w
            per_ticker_events[ev.symbol].append((ev, eff_sev))

        scores: Dict[str, float] = {}
        for ticker, evs in per_ticker_events.items():
            if not evs:
                continue

            # Severity component
            total_sev = sum(s for _, s in evs)

            # Diversity: more distinct event types → stronger pressure
            event_types: Set[str] = {e.event_type for e, _ in evs}
            diversity_factor = 1.0 + 0.15 * max(0, len(event_types) - 1)

            # Non-linear escalation
            raw_score = total_sev * diversity_factor
            # Squash to 0–10 with saturation
            score = 10 * (1 - exp(-raw_score / 12.0))
            scores[ticker] = min(10.0, score)

        return scores























