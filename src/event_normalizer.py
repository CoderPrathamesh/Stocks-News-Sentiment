"""
Event normalization: Map NSE/BSE categories to controlled taxonomy.

This module provides a controlled vocabulary for event classification,
enabling consistent downstream processing and ML training.
"""

from __future__ import annotations

from typing import Dict, List, Optional


# Controlled taxonomy for event types
EVENT_TYPES = [
    "REGULATORY_ACTION",
    "REGULATORY_CLARIFICATION",
    "LITIGATION",
    "FINANCIAL_STRESS",
    "CREDIT_RATING_ACTION",
    "CAPITAL_RAISE",
    "EQUITY_DILUTION",
    "MANAGEMENT_CHANGE",
    "OPERATIONAL_ISSUE",
    "GUIDANCE_UPDATE",
    "ORDER_WIN",
    "ROUTINE_COMPLIANCE",
    "INVESTOR_MEET",
    "PRESS_RELEASE",
    "OTHER",
]

# Mapping from NSE category strings (case-insensitive) to normalized event_type
NSE_CATEGORY_MAP: Dict[str, str] = {
    # Regulatory & Legal
    "action(s) taken or orders passed": "REGULATORY_ACTION",
    "action(s) initiated or orders passed": "REGULATORY_ACTION",
    "granting/withdrawal/surrender/cancellation/suspension of key licenses/ regulatory approvals": "REGULATORY_ACTION",
    "news verification": "REGULATORY_CLARIFICATION",
    "rumour verification": "REGULATORY_CLARIFICATION",
    "pendency of litigation(s)/dispute(s) or the outcome impacting the company": "LITIGATION",
    "suspension of trading": "REGULATORY_ACTION",
    "clarification - financial results": "REGULATORY_CLARIFICATION",
    # Financial & Credit
    "credit rating": "CREDIT_RATING_ACTION",
    "credit rating- revision": "CREDIT_RATING_ACTION",
    "credit rating- others": "CREDIT_RATING_ACTION",
    "allotment of securities": "EQUITY_DILUTION",
    "esop/esos/esps": "EQUITY_DILUTION",
    "preferential issue": "CAPITAL_RAISE",
    "issue of securities": "CAPITAL_RAISE",
    "rights issue": "CAPITAL_RAISE",
    # Management
    "appointment": "MANAGEMENT_CHANGE",
    "cessation": "MANAGEMENT_CHANGE",
    "resignation": "MANAGEMENT_CHANGE",
    "resignation of independent director": "MANAGEMENT_CHANGE",
    "change in director(s)": "MANAGEMENT_CHANGE",
    "change in management": "MANAGEMENT_CHANGE",
    "change in auditors": "MANAGEMENT_CHANGE",
    # Operational
    "bagging/receiving of orders/contracts": "ORDER_WIN",
    "acquisition": "OTHER",  # Could be positive or negative, needs context
    "general updates": "OTHER",  # Needs deep inspection
    "updates": "OTHER",  # Needs deep inspection
    # Routine Compliance
    "trading window": "ROUTINE_COMPLIANCE",
    "outcome of board meeting": "ROUTINE_COMPLIANCE",
    "board meeting intimation": "ROUTINE_COMPLIANCE",
    "shareholders meeting": "ROUTINE_COMPLIANCE",
    "agm notice": "ROUTINE_COMPLIANCE",
    "voting result": "ROUTINE_COMPLIANCE",
    "scrutinizer report": "ROUTINE_COMPLIANCE",
    "copy of newspaper publication": "ROUTINE_COMPLIANCE",
    "record date": "ROUTINE_COMPLIANCE",
    "dividend": "ROUTINE_COMPLIANCE",
    # Investor Relations
    "analysts/institutional investor meet/con. call updates": "INVESTOR_MEET",
    "investor presentation": "INVESTOR_MEET",
    # Press & Media
    "press release": "PRESS_RELEASE",
    # Other
    "incorporation": "OTHER",
    "agreements": "OTHER",
    "amendment to aoa/moa": "ROUTINE_COMPLIANCE",
}


def normalize_event_type(nse_category: str, headline: str = "", summary: str = "") -> str:
    """
    Map NSE category + context to normalized event_type.

    Parameters
    ----------
    nse_category : str
        Raw NSE category string (e.g., "General Updates", "Action(s) taken or orders passed")
    headline : str
        Headline text for context
    summary : str
        Summary/body text for context

    Returns
    -------
    str
        Normalized event_type from EVENT_TYPES
    """
    if not nse_category:
        return "OTHER"

    cat_lower = nse_category.lower().strip()

    # Direct mapping
    if cat_lower in NSE_CATEGORY_MAP:
        mapped = NSE_CATEGORY_MAP[cat_lower]
        # Special handling for "General Updates" - check if it contains serious content
        if mapped == "OTHER" and cat_lower == "general updates":
            text = (headline + " " + summary).lower()
            # Check for serious regulatory/operational issues hidden in "General Updates"
            serious_keywords = [
                "fda",
                "oai",
                "regulatory",
                "penalty",
                "litigation",
                "dispute",
                "demand notice",
                "order passed",
                "suspension",
                "cancellation",
                "fraud",  # Loan fraud, banking fraud
                "loan fraud",  # Specific banking fraud
                "reported to rbi",  # RBI fraud reporting
                "rbi",  # RBI mentions (often with fraud in context)
            ]
            if any(kw in text for kw in serious_keywords):
                return "REGULATORY_ACTION"
        return mapped

    # Fuzzy matching for common variations
    for nse_key, normalized in NSE_CATEGORY_MAP.items():
        if nse_key in cat_lower or cat_lower in nse_key:
            return normalized

    return "OTHER"


def get_event_type_description(event_type: str) -> str:
    """Return human-readable description of event type."""
    descriptions = {
        "REGULATORY_ACTION": "Regulatory enforcement or action",
        "REGULATORY_CLARIFICATION": "Exchange/regulator seeking clarification",
        "LITIGATION": "Legal disputes or pending litigation",
        "FINANCIAL_STRESS": "Financial distress indicators",
        "CREDIT_RATING_ACTION": "Credit rating changes",
        "CAPITAL_RAISE": "Capital raising activities",
        "EQUITY_DILUTION": "Equity dilution events",
        "MANAGEMENT_CHANGE": "Management personnel changes",
        "OPERATIONAL_ISSUE": "Operational disruptions or issues",
        "GUIDANCE_UPDATE": "Earnings/guidance updates",
        "ORDER_WIN": "Order/contract wins",
        "ROUTINE_COMPLIANCE": "Routine compliance disclosures",
        "INVESTOR_MEET": "Investor relations activities",
        "PRESS_RELEASE": "Press releases",
        "OTHER": "Unclassified or other events",
    }
    return descriptions.get(event_type, "Unknown event type")




















