"""
Routine filtering logic - deterministic classification of routine disclosures.

Sets is_routine=True and impact_direction=NEUTRAL for routine items.
"""

from __future__ import annotations

from typing import Any, Dict, List


# Event types that are always routine
ROUTINE_EVENT_TYPES = [
    "ROUTINE_COMPLIANCE",
    "INVESTOR_MEET",
    "PRESS_RELEASE",  # Usually neutral/positive, not negative risk
]

# Keywords/phrases that indicate routine disclosures
ROUTINE_KEYWORDS = [
    "outcome of board meeting",
    "board meeting intimation",
    "agm notice",
    "voting result",
    "scrutinizer report",
    "shareholding pattern",
    "compliance certificate",
    "trading window",
    "trading window closure",
    "esop",
    "esos",
    "esps",
    "allotment of",
    "copy of newspaper publication",
    "newspaper publication",
    "record date",
    "dividend",
    "analyst meet",
    "investor meet",
    "institutional investor meet",
    "incorporation",
    "amendment to aoa/moa",
    # Corporate action related trading suspensions (routine, not negative)
    "call money",  # Trading suspension for call money collection
    "partly paid",  # Partly paid shares related actions
    "partly paid-up",  # Alternative spelling
    "rights issue",  # Rights issue related corporate actions
]


def is_routine_disclosure(enriched_record: Dict[str, Any]) -> bool:
    """
    Determine if an enriched record is a routine disclosure.

    Parameters
    ----------
    enriched_record : Dict[str, Any]
        Enriched record

    Returns
    -------
    bool
        True if routine, False otherwise
    """
    event_type = str(enriched_record.get("event_type", "")).upper()
    if event_type in ROUTINE_EVENT_TYPES:
        return True

    # Check text content
    text = (
        str(enriched_record.get("headline", ""))
        + " "
        + str(enriched_record.get("summary", ""))
        + " "
        + str(enriched_record.get("clean_text", ""))
    ).lower()

    for keyword in ROUTINE_KEYWORDS:
        if keyword in text:
            return True

    return False


def apply_routine_filter(enriched_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply routine filter to an enriched record.

    Sets:
    - is_routine = True
    - impact_direction = NEUTRAL
    - severity_score <= 1.0
    - is_potentially_negative = False
    """
    if is_routine_disclosure(enriched_record):
        enriched_record["is_routine"] = True
        enriched_record["impact_direction"] = "NEUTRAL"
        enriched_record["severity_score"] = min(1.0, float(enriched_record.get("severity_score", 0.0)))
        enriched_record["is_potentially_negative"] = False

    return enriched_record













