from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from math import exp
from typing import Dict, Iterable, List, Set, Tuple

from .models import Event


class RollingNegativePressure:
    """
    Rolling 7–14 day negative pressure model for each ticker.

    - Uses exponential decay with configurable half-life
    - Aggregates severity * credibility
    - Rewards diversity of event types
    - Applies a non-linear escalation so clusters of events stand out
    """

    def __init__(self, window_days: int = 14, half_life_days: int = 7) -> None:
        self.window = timedelta(days=window_days)
        self.half_life = half_life_days

    def _decay_weight(self, age_days: float) -> float:
        # exponential decay: weight = 0.5 ** (age_days / half_life)
        return 0.5 ** (age_days / self.half_life)

    def compute_scores(
        self,
        events: Iterable[Event],
        now: datetime | None = None,
    ) -> Dict[str, float]:
        """
        Return downside pressure scores in [0, 10] per ticker.
        """
        now = now or datetime.utcnow()

        per_ticker_events: Dict[str, List[Tuple[Event, float]]] = defaultdict(list)

        for ev in events:
            age_td = now - ev.timestamp
            age = age_td.days + age_td.seconds / 86400.0
            if age > self.window.days:
                continue
            w = self._decay_weight(age)
            eff_sev = ev.base_severity * ev.credibility * w
            per_ticker_events[ev.ticker].append((ev, eff_sev))

        scores: Dict[str, float] = {}
        for ticker, evs in per_ticker_events.items():
            if not evs:
                continue

            total_sev = sum(s for _, s in evs)

            # Diversity bonus: more distinct event types → stronger pressure
            event_types: Set[str] = {e.event_type for e, _ in evs}
            diversity_factor = 1.0 + 0.15 * max(0, len(event_types) - 1)

            # Non-linear escalation so multiple events snowball
            raw_score = total_sev * diversity_factor
            score = 10 * (1 - exp(-raw_score / 12.0))
            scores[ticker] = min(10.0, score)

        return scores


























