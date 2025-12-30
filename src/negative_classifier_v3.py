"""
Negative risk classifier - contextual meaning-based classification.

Only flags events as negative if contextual meaning implies downside risk.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

# This module works with dict records, not dataclasses


# High-confidence negative indicators
NEGATIVE_INDICATORS: List[Tuple[str, float]] = [
    # Regulatory actions
    ("penalty", 7.0),
    ("fine imposed", 7.5),
    ("fine of", 7.5),
    ("rbi.*penalty", 8.0),
    ("rbi.*imposed.*penalty", 8.0),  # RBI imposed a penalty
    ("penalty.*imposed.*rbi", 8.0),  # Penalty imposed by RBI
    ("rbi.*penalty.*of", 8.0),  # RBI penalty of [amount]
    ("sebi.*imposed.*penalty", 8.0),  # SEBI imposed a penalty
    ("penalty.*imposed.*sebi", 8.0),  # Penalty imposed by SEBI
    ("sebi.*penalty.*of", 8.0),  # SEBI penalty of [amount]
    ("penalty.*by.*sebi", 8.0),  # Penalty by SEBI
    ("sebi.*levied.*penalty", 8.0),  # SEBI levied penalty
    ("fda.*oai", 9.5),  # FDA OAI is very serious
    ("fda.*warning letter", 8.5),
    ("license.*suspended", 9.0),
    ("license.*cancelled", 9.5),
    ("suspension of trading", 9.0),
    # Rating actions
    ("rating.*downgraded", 8.0),
    ("downgraded.*rating", 8.0),
    ("negative outlook", 7.5),
    # Financial stress
    ("default", 9.5),
    ("liquidity.*stress", 8.5),
    ("liquidity.*issue", 8.0),
    ("debt.*issue", 7.5),
    # Guidance cuts
    ("guidance.*cut", 8.5),
    ("lower.*guidance", 8.0),
    ("profit.*warning", 8.5),
    ("revised.*downward", 8.0),
    # Legal/regulatory - ENHANCED SECTION
    ("demand notice", 7.5),
    ("order passed.*gst", 7.5),
    ("order passed.*tax", 7.5),
    ("order received.*gst", 7.5),  # NEW: catches "order received from GST"
    ("order.*received.*gst", 7.5),  # NEW: more flexible
    ("order received.*tax", 7.5),  # NEW
    ("order.*received.*tax", 7.5),  # NEW
    ("gst.*order", 7.0),  # NEW: catches any GST order mention
    ("tax.*order", 7.0),  # NEW: catches any tax order mention
    ("penalty.*crore", 8.5),  # NEW: large monetary penalties
    (".*crore.*penalty", 8.5),  # NEW: penalty with large amount
    ("tax dues", 7.5),  # NEW: tax dues are negative
    ("alleged.*tax", 7.0),  # NEW: alleged tax issues
    ("show cause notice", 7.0),
    ("fir.*filed", 8.0),
    ("police.*fir", 8.0),
    ("sfio.*scanner", 8.5),
    ("under.*scanner", 7.5),
    ("watchdog.*summons", 8.0),
    ("sebi.*examining", 7.5),
    ("failed.*disclosures", 8.0),
    # Operational risks
    ("plant.*shutdown", 8.0),
    ("production.*halt", 8.5),
    ("major.*accident", 9.0),
    ("safety.*incident", 8.5),
    ("dgca.*issues", 8.5),
    ("flight.*cancellation", 7.0),
    # Litigation
    ("litigation", 7.0),
    ("pendency.*litigation", 7.5),
    ("dispute", 6.5),
    # Fraud & Financial Crimes
    ("loan fraud", 9.5),  # Banking fraud is very serious
    ("fraud.*crore", 9.5),  # Large fraud amounts
    (".*crore.*fraud", 9.5),
    ("banking fraud", 9.5),
    ("reported to rbi.*fraud", 9.5),  # RBI fraud reporting
    ("rbi.*fraud", 9.5),
    ("financial fraud", 9.0),
    ("fraud.*reported", 9.0),  # Fraud being reported
    ("fraud", 8.5),  # General fraud (may catch false positives, but better than missing it)
]


def classify_negative_risk(enriched_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classify negative risk for an enriched record.

    Sets:
    - is_potentially_negative = True if risk detected
    - impact_direction = NEGATIVE or WATCH
    - severity_score >= 4.0 if negative
    - confidence_score based on indicator strength
    - flag_reason explaining why flagged
    """
    # Skip if already marked as routine
    if enriched_record.get("is_routine", False):
        return enriched_record

    text = (
        str(enriched_record.get("headline", ""))
        + " "
        + str(enriched_record.get("summary", ""))
        + " "
        + str(enriched_record.get("clean_text", ""))
    ).lower()
    
    # Also check raw data for attachment filenames (fraud often in PDF names)
    # This helps catch cases where fraud is only mentioned in attachment filename
    if "raw" in enriched_record:
        raw_data = enriched_record.get("raw", {})
        if isinstance(raw_data, dict):
            attchmnt_file = str(raw_data.get("attchmntFile", "") or "")
            if attchmnt_file:
                text += " " + attchmnt_file.lower()

    event_type = str(enriched_record.get("event_type", "")).upper()

    # Check event type first
    if event_type in [
        "REGULATORY_ACTION",
        "LITIGATION",
        "FINANCIAL_STRESS",
        "OPERATIONAL_ISSUE",
    ]:
        enriched_record["is_potentially_negative"] = True
        enriched_record["impact_direction"] = "NEGATIVE"
        enriched_record["severity_score"] = 7.0
        enriched_record["confidence_score"] = 0.85
        enriched_record["flag_reason"] = f"EVENT_TYPE_{event_type}"
        return enriched_record

    if event_type == "REGULATORY_CLARIFICATION":
        enriched_record["is_potentially_negative"] = True
        enriched_record["impact_direction"] = "WATCH"
        enriched_record["severity_score"] = 5.0
        enriched_record["confidence_score"] = 0.70
        enriched_record["flag_reason"] = "EXCHANGE_CLARIFICATION"
        return enriched_record

    # Pattern matching for negative indicators
    best_match: Tuple[str, float] | None = None
    for pattern, severity in NEGATIVE_INDICATORS:
        if re.search(pattern, text):
            if best_match is None or severity > best_match[1]:
                best_match = (pattern, severity)

    if best_match:
        pattern, severity = best_match
        enriched_record["is_potentially_negative"] = True
        enriched_record["impact_direction"] = "NEGATIVE" if severity >= 8.0 else "WATCH"
        enriched_record["severity_score"] = severity
        enriched_record["confidence_score"] = min(0.95, 0.6 + (severity / 20.0))
        enriched_record["flag_reason"] = f"PATTERN_MATCH_{pattern[:30]}"
        return enriched_record

    # Default: not negative
    return enriched_record

