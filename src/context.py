from __future__ import annotations

from .models import Event


def enrich_with_context(event: Event) -> Event:
    """
    Optional hook for LLM-based context interpretation.

    For now this uses a deterministic heuristic so outputs are reproducible.
    You can later plug in an LLM here which:
      - MUST NOT hallucinate facts
      - Only reasons based on the event.raw_news contents
      - Prefers false negatives over false positives
    """
    # Simple heuristic example: very long, detailed disclosures likely imply
    # materiality, so we can bump risk one notch for medium events.
    text_len = len(event.raw_news.body)
    if event.downside_risk == "medium" and text_len > 1200:
        event.downside_risk = "high"
        event.justification += " | Long detailed disclosure suggests materiality."

    return event


























