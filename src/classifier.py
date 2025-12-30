from __future__ import annotations

from typing import List, Tuple

from .models import Event, NewsItem


# (keyword, event_type, base_severity)
EVENT_RULES: List[Tuple[str, str, float]] = [
    ("penalty", "Monetary Penalty / Fine", 6.5),
    ("fine imposed", "Monetary Penalty / Fine", 7.0),
    ("show cause notice", "Regulatory / License Action", 7.5),
    ("license suspended", "Regulatory / License Action", 9.0),
    ("licence suspended", "Regulatory / License Action", 9.0),
    ("license cancelled", "Regulatory / License Action", 9.5),
    ("licence cancelled", "Regulatory / License Action", 9.5),
    ("profit warning", "Guidance Cut / Profit Warning", 8.5),
    ("lower guidance", "Guidance Cut / Profit Warning", 7.5),
    ("cuts guidance", "Guidance Cut / Profit Warning", 8.0),
    ("guidance revised down", "Guidance Cut / Profit Warning", 8.0),
    ("downgraded by", "Credit Rating Downgrade", 8.0),
    ("rating downgraded", "Credit Rating Downgrade", 8.5),
    ("downgraded to", "Credit Rating Downgrade", 8.0),
    ("liquidity stress", "Financial Stress / Liquidity Issues", 8.0),
    ("liquidity issue", "Financial Stress / Liquidity Issues", 7.5),
    ("default", "Financial Stress / Liquidity Issues", 9.0),
    ("plant shutdown", "Operational Disruption", 7.5),
    ("production halt", "Operational Disruption", 8.0),
    ("production disrupted", "Operational Disruption", 7.5),
    ("strike", "Operational Disruption", 7.0),
    ("resignation of", "Management Instability", 6.5),
    ("cfo resigns", "Management Instability", 7.5),
    ("ceo resigns", "Management Instability", 8.0),
    ("managing director resigns", "Management Instability", 8.0),
    ("safety incident", "Safety / Compliance Failure", 8.0),
    ("accident at", "Safety / Compliance Failure", 8.5),
    ("dgca issues", "Safety / Compliance Failure", 8.5),
    ("show-cause notice by dgca", "Safety / Compliance Failure", 9.0),
    # Broader operational / safety patterns (conservative but a bit wider net)
    ("fire at", "Safety / Compliance Failure", 8.0),
    ("major accident", "Safety / Compliance Failure", 8.5),
    ("operational issue", "Operational Disruption", 6.5),
    ("service disruption", "Operational Disruption", 7.0),
    ("flight cancellations", "Operational Disruption", 7.5),
    ("cancellation of flights", "Operational Disruption", 7.5),
]


def source_credibility(source: str) -> float:
    s = source.lower()
    if any(x in s for x in ["bse", "nse", "exchange"]):
        return 1.0
    if any(x in s for x in ["moneycontrol", "economic times", "bloomberg", "reuters"]):
        return 0.9
    return 0.7


def classify_news(news: NewsItem) -> Event | None:
    """
    Convert a raw news item into a structured Event, or None if not clearly negative.

    Prefer false negatives over false positives: if we cannot confidently map
    to a negative event type, we return None.
    """
    text = (news.headline + " " + news.body).lower()

    best_rule = None
    for kw, ev_type, base_sev in EVENT_RULES:
        if kw in text:
            if best_rule is None or base_sev > best_rule[2]:
                best_rule = (kw, ev_type, base_sev)

    if best_rule is None:
        return None

    _, event_type, base_severity = best_rule
    cred = source_credibility(news.source)

    eff = base_severity * cred
    if eff >= 8.0:
        downside = "high"
    elif eff >= 5.0:
        downside = "medium"
    else:
        downside = "low"

    return Event(
        ticker=news.ticker,
        source=news.source,
        timestamp=news.timestamp,
        event_type=event_type,
        is_routine=False,
        is_negative=True,
        base_severity=base_severity,
        credibility=cred,
        downside_risk=downside,
        justification=f"{event_type} detected via keyword rules",
        raw_news=news,
    )


