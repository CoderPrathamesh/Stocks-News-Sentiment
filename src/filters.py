from __future__ import annotations

from typing import Iterable, List

from .models import NewsItem


ROUTINE_KEYWORDS = [
    "outcome of board meeting",
    "board meeting intimation",
    "agm notice",
    "voting result",
    "scrutinizer report",
    "shareholding pattern",
    "compliance certificate",
    "intimation of closure of trading window",
    "regulation 30 - press release",
    "regulation 7(3)",
    "regulation 40(9)",
    "statement of investor complaints",
]


def is_routine(news: NewsItem) -> bool:
    """Return True if the news item looks like a routine / non-impactful filing."""
    text = (news.headline + " " + news.body).lower()
    return any(kw in text for kw in ROUTINE_KEYWORDS)


def filter_routine(news_items: Iterable[NewsItem]) -> List[NewsItem]:
    """Filter out routine news items that are unlikely to drive downside risk."""
    return [n for n in news_items if not is_routine(n)]


























