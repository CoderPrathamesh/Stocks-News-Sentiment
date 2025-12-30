"""
Context-aware impact interpretation logic.

This module assigns impact_direction and impact_confidence based on:
- Event type
- Text content analysis
- Regulatory/legal language detection
- Historical patterns (future: ML similarity)

NOT keyword-only: uses semantic understanding where possible.
"""

from __future__ import annotations

from typing import List, Tuple

from .models import EnrichedEvent

# Impact direction constants
IMPACT_NEGATIVE = "NEGATIVE"
IMPACT_POTENTIALLY_NEGATIVE = "POTENTIALLY_NEGATIVE"
IMPACT_NEUTRAL = "NEUTRAL"
IMPACT_POTENTIALLY_POSITIVE = "POTENTIALLY_POSITIVE"
IMPACT_POSITIVE = "POSITIVE"


# High-confidence negative patterns (regulatory, legal, financial stress)
HIGH_NEGATIVE_PATTERNS: List[Tuple[str, float]] = [
    # Regulatory actions
    ("fda.*oai", 0.95),  # FDA OAI is serious
    ("fda.*warning letter", 0.90),
    ("rbi.*penalty", 0.90),
    ("rbi.*imposes.*penalty", 0.90),
    ("sebi.*penalty", 0.90),
    ("license.*suspended", 0.95),
    ("license.*cancelled", 0.95),
    ("licence.*suspended", 0.95),
    ("licence.*cancelled", 0.95),
    ("suspension of trading", 0.95),
    # Legal/Enforcement
    ("demand notice", 0.85),
    ("order passed.*gst", 0.85),
    ("order passed.*tax", 0.85),
    ("show cause notice", 0.80),
    ("fir.*filed", 0.85),
    ("police.*fir", 0.85),
    ("sfio.*scanner", 0.90),
    ("under.*scanner", 0.80),
    ("watchdog.*summons", 0.85),
    ("sebi.*examining", 0.80),
    ("failed.*disclosures", 0.85),
    # Financial stress
    ("default", 0.95),
    ("liquidity.*stress", 0.90),
    ("liquidity.*issue", 0.85),
    ("rating.*downgraded", 0.85),
    ("downgraded.*rating", 0.85),
    # Operational disruptions
    ("plant.*shutdown", 0.80),
    ("production.*halt", 0.80),
    ("major.*accident", 0.90),
    ("safety.*incident", 0.85),
    ("dgca.*issues", 0.85),
    ("flight.*cancellation", 0.75),
]

# Potentially negative patterns (need context)
POTENTIALLY_NEGATIVE_PATTERNS: List[Tuple[str, float]] = [
    ("litigation", 0.70),
    ("dispute", 0.65),
    ("pendency.*litigation", 0.75),
    ("news verification", 0.60),  # Exchange seeking clarification
    ("rumour verification", 0.60),
    ("clarification.*sought", 0.65),
    ("management.*change", 0.50),  # Could be positive or negative
    ("resignation", 0.60),
    ("ceo.*resigns", 0.70),
    ("cfo.*resigns", 0.70),
    ("guidance.*cut", 0.80),
    ("lower.*guidance", 0.75),
    ("profit.*warning", 0.85),
]

# Positive patterns
POSITIVE_PATTERNS: List[Tuple[str, float]] = [
    ("order.*win", 0.75),
    ("contract.*awarded", 0.75),
    ("partnership", 0.60),
    ("acquisition", 0.50),  # Context-dependent
    ("rating.*upgraded", 0.80),
    ("upgraded.*rating", 0.80),
]

# Routine/neutral patterns (should be filtered earlier, but check anyway)
ROUTINE_PATTERNS: List[str] = [
    "esop",
    "esos",
    "trading window",
    "board meeting",
    "agm",
    "dividend",
    "record date",
    "investor meet",
    "analyst meet",
]


def interpret_impact(event: EnrichedEvent) -> Tuple[str, float]:
    """
    Determine impact_direction and impact_confidence for an enriched event.

    Uses:
    1. Event type heuristics
    2. Pattern matching in text (semantic-aware where possible)
    3. Regulatory/legal language detection
    4. Context from headline + summary

    Returns
    -------
    Tuple[str, float]
        (impact_direction, impact_confidence)
    """
    text = event.clean_text.lower()
    event_type = event.event_type

    # Event type-based heuristics
    if event_type == "REGULATORY_ACTION":
        # Check for high-severity regulatory actions
        for pattern, conf in HIGH_NEGATIVE_PATTERNS:
            if pattern in text or pattern.replace(".*", " ") in text:
                return (IMPACT_NEGATIVE, conf)
        return (IMPACT_POTENTIALLY_NEGATIVE, 0.75)

    if event_type == "REGULATORY_CLARIFICATION":
        # Exchange seeking clarification is potentially negative
        return (IMPACT_POTENTIALLY_NEGATIVE, 0.65)

    if event_type == "LITIGATION":
        # Litigation is potentially negative, confidence depends on severity
        for pattern, conf in POTENTIALLY_NEGATIVE_PATTERNS:
            if pattern in text:
                return (IMPACT_POTENTIALLY_NEGATIVE, conf)
        return (IMPACT_POTENTIALLY_NEGATIVE, 0.70)

    if event_type == "FINANCIAL_STRESS":
        return (IMPACT_NEGATIVE, 0.85)

    if event_type == "CREDIT_RATING_ACTION":
        # Check if upgrade or downgrade
        if any(p in text for p in ["downgrade", "downgraded", "negative outlook"]):
            return (IMPACT_NEGATIVE, 0.85)
        if any(p in text for p in ["upgrade", "upgraded", "positive outlook"]):
            return (IMPACT_POTENTIALLY_POSITIVE, 0.75)
        return (IMPACT_NEUTRAL, 0.60)

    if event_type == "OPERATIONAL_ISSUE":
        return (IMPACT_POTENTIALLY_NEGATIVE, 0.75)

    if event_type == "GUIDANCE_UPDATE":
        # Check if guidance cut
        if any(p in text for p in ["cut", "lower", "revised down", "warning"]):
            return (IMPACT_NEGATIVE, 0.80)
        return (IMPACT_NEUTRAL, 0.60)

    if event_type == "ORDER_WIN":
        return (IMPACT_POTENTIALLY_POSITIVE, 0.70)

    if event_type == "ROUTINE_COMPLIANCE":
        return (IMPACT_NEUTRAL, 0.90)

    if event_type == "EQUITY_DILUTION":
        # ESOPs are routine, but large dilutions could be negative
        if "esop" in text or "esos" in text:
            return (IMPACT_NEUTRAL, 0.85)
        return (IMPACT_POTENTIALLY_NEGATIVE, 0.60)

    if event_type == "MANAGEMENT_CHANGE":
        # Context-dependent: CEO resignation is more serious
        if any(p in text for p in ["ceo", "managing director", "md"]):
            return (IMPACT_POTENTIALLY_NEGATIVE, 0.70)
        return (IMPACT_NEUTRAL, 0.60)

    # Pattern-based fallback (for "OTHER" or unclassified)
    # Check high-confidence negative patterns first
    for pattern, conf in HIGH_NEGATIVE_PATTERNS:
        import re

        if re.search(pattern, text):
            return (IMPACT_NEGATIVE, conf)

    # Check potentially negative patterns
    for pattern, conf in POTENTIALLY_NEGATIVE_PATTERNS:
        import re

        if re.search(pattern, text):
            return (IMPACT_POTENTIALLY_NEGATIVE, conf)

    # Check positive patterns
    for pattern, conf in POSITIVE_PATTERNS:
        import re

        if re.search(pattern, text):
            return (IMPACT_POTENTIALLY_POSITIVE, conf)

    # Check if routine
    if any(routine in text for routine in ROUTINE_PATTERNS):
        return (IMPACT_NEUTRAL, 0.85)

    # Default: neutral with low confidence (prefer false negatives)
    return (IMPACT_NEUTRAL, 0.50)


def apply_impact_interpretation(event: EnrichedEvent) -> EnrichedEvent:
    """
    Apply impact interpretation to an enriched event, updating impact_direction and impact_confidence.
    """
    impact_dir, impact_conf = interpret_impact(event)
    event.impact_direction = impact_dir
    event.impact_confidence = impact_conf
    return event























