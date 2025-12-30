# Architecture v3 - Separated Pipeline with Daily File Organization

## Overview

The system has been restructured to separate raw ingestion, enrichment, filtering, and logging, with daily file organization and deterministic logic.

## Core Principles

1. **Raw data is never modified** - All incoming data saved exactly as received
2. **Separated layers** - Ingestion → Enrichment → Filtering → Classification → Logging
3. **Daily organization** - All files organized by date in separate folders
4. **Deterministic logic** - No ML yet, only rule-based classification
5. **Explainability** - Every flag has a reason
6. **Fail-safe** - Raw data saved even if enrichment fails

## Directory Structure

```
project_root/
├── data/
│   ├── raw/
│   │   └── YYYY-MM-DD/
│   │       └── raw_announcements.csv
│   ├── enriched/
│   │   └── YYYY-MM-DD/
│   │       └── enriched_events.csv
│   └── signals/
│       └── YYYY-MM-DD/
│           └── negative_signals.csv
└── logs/
    └── YYYY-MM-DD/
        └── pipeline.log
```

## Pipeline Flow

### 1. Raw Ingestion (`src/raw_writer.py`)
- Fetches articles from NSE/BSE collectors
- Saves to `data/raw/YYYY-MM-DD/raw_announcements.csv`
- **Never modifies** raw data
- Appends only new records (duplicate detection)

### 2. Enrichment Layer (`src/enrichment_v3.py`)
- Transforms raw → enriched schema
- Adds: `event_type`, `clean_text`, `parser_version`
- Saves to `data/enriched/YYYY-MM-DD/enriched_events.csv`

### 3. Routine Filtering (`src/routine_filter_v3.py`)
- Deterministic classification of routine disclosures
- Sets: `is_routine=True`, `impact_direction=NEUTRAL`, `severity_score<=1.0`
- Filters: board meetings, ESOPs, analyst calls, etc.

### 4. Negative Risk Classification (`src/negative_classifier_v3.py`)
- Contextual meaning-based classification
- Only flags if downside risk is implied
- Sets: `is_potentially_negative=True`, `impact_direction=NEGATIVE/WATCH`, `severity_score>=4.0`
- Updates enriched records

### 5. Signal Generation (`src/signals_writer.py`)
- Extracts only negative/watch signals
- Saves to `data/signals/YYYY-MM-DD/negative_signals.csv`
- This is the **final output for human review**

### 6. Process Logging (`src/process_logger.py`)
- Logs execution statistics
- Saves to `logs/YYYY-MM-DD/pipeline.log`
- Includes: counts, versions, execution time

## Enriched Schema

Each enriched record contains:

```python
{
    "symbol": str,
    "source": str,
    "published_at": str,
    "headline": str,
    "summary": str,
    "clean_text": str,
    "event_type": str,  # Normalized taxonomy
    "is_routine": bool,
    "is_potentially_negative": bool,
    "impact_direction": str,  # NEGATIVE | NEUTRAL | POSITIVE | WATCH
    "severity_score": float,  # 0.0 - 10.0
    "confidence_score": float,  # 0.0 - 1.0
    "flag_reason": str,  # Comma-separated reasons
    "parser_version": str,
    "human_label": str,  # Empty by default, for future ML
    "human_comment": str,  # Empty by default, for future ML
    "raw_id": str,
}
```

## Event Type Taxonomy

Normalized event types (from `src/event_normalizer.py`):

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

## Routine Filtering Rules

These default to `is_routine=True`, `impact_direction=NEUTRAL`:

- Board meetings
- Analyst/investor calls
- ESOP/ESOS/ESPS allotments
- Newspaper publications
- Trading window closures
- Record dates / dividends
- Incorporations (unless flagged)
- Investor presentations

## Negative Risk Indicators

Only flagged if contextual meaning implies downside risk:

- **Regulatory**: Penalties, fines, license suspensions, FDA OAI
- **Financial**: Rating downgrades, liquidity stress, defaults
- **Legal**: Tax demands, FIRs, litigation, show-cause notices
- **Operational**: Plant shutdowns, safety incidents, production halts
- **Clarifications**: Exchange seeking clarification (WATCH)

## Usage

```bash
python batch_collect.py --universe fo_universe.csv --parser-version v3.0
```

## Output Files

After each run, check:

1. **Raw data**: `data/raw/YYYY-MM-DD/raw_announcements.csv`
   - All incoming data, never modified

2. **Enriched data**: `data/enriched/YYYY-MM-DD/enriched_events.csv`
   - All enriched records with full schema

3. **Signals**: `data/signals/YYYY-MM-DD/negative_signals.csv`
   - Only negative/watch events for human review

4. **Logs**: `logs/YYYY-MM-DD/pipeline.log`
   - Execution statistics and version info

## Success Criteria

✅ Daily folders created automatically  
✅ Raw and enriched data are separate  
✅ Routine disclosures filtered out  
✅ Regulatory and financial risks surfaced  
✅ Output is auditable and explainable  
✅ Zero false negatives for material risks (preferred over false positives)

## Future ML Integration

The system is designed for future ML training:

- `human_label` and `human_comment` fields ready for manual labeling
- Enriched schema contains all features needed for training
- Deterministic logic provides baseline for comparison
- Process logs track parser/model versions

When sufficient labeled data exists, ML can be added without changing the architecture.























