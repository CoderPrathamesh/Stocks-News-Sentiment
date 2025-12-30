# Downside Risk Detection System - Refactor Summary

## Overview

The system has been refactored from a keyword-based classifier to a **context-aware, enrichment-based pipeline** that:

1. **Normalizes events** into a controlled taxonomy
2. **Enriches data** with impact direction, confidence, and flag reasons
3. **Interprets impact** using context-aware logic (not just keywords)
4. **Outputs ranked signals** showing only NEGATIVE and POTENTIALLY_NEGATIVE events

## Key Changes

### New Modules

1. **`src/event_normalizer.py`**
   - Maps NSE categories to controlled taxonomy (REGULATORY_ACTION, LITIGATION, etc.)
   - Handles "General Updates" that hide serious issues

2. **`src/enrichment.py`**
   - Transforms raw NewsItem → EnrichedEvent
   - Adds: clean_text, event_type, impact_direction, impact_confidence, flag_reason
   - Prepares data for ML training

3. **`src/impact_interpreter.py`**
   - Context-aware impact interpretation
   - Uses pattern matching + event type heuristics
   - Assigns impact_direction (NEGATIVE, POTENTIALLY_NEGATIVE, NEUTRAL, etc.)
   - Assigns impact_confidence (0.0 - 1.0)

4. **`src/classifier_v2.py`**
   - Replaces old keyword-only classifier
   - Uses enrichment + impact interpretation
   - Filters to only NEGATIVE/POTENTIALLY_NEGATIVE

5. **`src/pipeline_v2.py`**
   - New pipeline using enrichment layer
   - Works with EnrichedEvent throughout

6. **`src/pressure_v2.py`**
   - Rolling pressure model for EnrichedEvent
   - Uses impact_direction and impact_confidence

7. **`src/signals_v2.py`**
   - Generates ranked signals with enrichment fields
   - Returns EnrichedSignal with event_type, impact_direction, etc.

8. **`src/feedback.py`**
   - Stores human feedback for ML training
   - Enables supervised learning in the future

### Updated Modules

- **`src/models.py`**: Added `EnrichedEvent` dataclass
- **`src/collectors/nse_filings.py`**: Extracts NSE category from API response
- **`batch_collect.py`**: Uses new pipeline_v2, outputs ranked list

## Usage

### Run with New Pipeline (Default)

```bash
python batch_collect.py --universe fo_universe.csv --no-context
```

This uses the new enrichment-based pipeline (v2) by default.

### Use Old Pipeline (if needed)

```bash
python batch_collect.py --universe fo_universe.csv --no-context --use-v1
```

### Output Format

The new pipeline outputs a **ranked list** at the end:

```
================================================================================
RANKED DOWNSIDE RISK SIGNALS
================================================================================
SYMBOL       EVENT_TYPE              IMPACT               CONF     SCORE    WHY_FLAGGED
--------------------------------------------------------------------------------
INDIGO       REGULATORY_CLARIFICATION POTENTIALLY_NEGATIVE  0.65     7.20     EXCHANGE_CLARIFICATION, REGULATOR_MENTION
SUNPHARMA    REGULATORY_ACTION        NEGATIVE              0.95     8.50     REGULATOR_MENTION, KEY_PHRASE_DETECTED
...
```

Only **NEGATIVE** and **POTENTIALLY_NEGATIVE** events are shown.

## Event Taxonomy

Controlled event types:
- `REGULATORY_ACTION`
- `REGULATORY_CLARIFICATION`
- `LITIGATION`
- `FINANCIAL_STRESS`
- `CREDIT_RATING_ACTION`
- `CAPITAL_RAISE`
- `EQUITY_DILUTION`
- `MANAGEMENT_CHANGE`
- `OPERATIONAL_ISSUE`
- `GUIDANCE_UPDATE`
- `ORDER_WIN`
- `ROUTINE_COMPLIANCE`
- `INVESTOR_MEET`
- `PRESS_RELEASE`
- `OTHER`

## Impact Interpretation

- **NEGATIVE**: High-confidence negative events (FDA OAI, penalties, suspensions)
- **POTENTIALLY_NEGATIVE**: Lower confidence but still risky (litigation, clarifications)
- **NEUTRAL**: Routine compliance, ESOPs, investor meets
- **POTENTIALLY_POSITIVE**: Order wins, partnerships
- **POSITIVE**: Rating upgrades (rarely flagged)

## Flag Reasons

Explainable reasons why events were flagged:
- `REGULATOR_MENTION`: RBI, SEBI, FDA, DGCA mentioned
- `LEGAL_LANGUAGE`: Litigation, FIR, demand notice, etc.
- `KEY_PHRASE_DETECTED`: Matched negative event patterns
- `EXCHANGE_CLARIFICATION`: Exchange seeking clarification
- `EVENT_TYPE_MATCHED`: Matched event type taxonomy

## What's Fixed

1. ✅ **"General Updates" now inspected** - Checks for serious regulatory issues hidden in generic categories
2. ✅ **Context-aware interpretation** - Not just keywords, uses event type + patterns
3. ✅ **Explainable flags** - Every signal has flag_reason explaining why
4. ✅ **Ranked output** - Signals sorted by severity
5. ✅ **ML-ready schema** - EnrichedEvent has all fields needed for training
6. ✅ **Feedback loop** - Human labels can be stored for supervised learning

## Next Steps (Future ML)

The system is designed to support ML training:

1. Collect human feedback using `FeedbackStore`
2. Train classifier on: event_type + text embeddings + historical price reaction
3. Predict: probability_of_negative_impact (next 1-7 days)

For now, it uses rule-based + similarity-based ranking.

## Testing

Test with the harness:

```bash
python test_harness.py
```

Or run on real data:

```bash
python batch_collect.py --universe fo_universe.csv --no-context
```

Check `signals.db` for stored signals, or view the ranked output at the end of the batch run.























