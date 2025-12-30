import argparse
import csv
import os
from typing import Iterable, Tuple

from src.collectors.nse_filings import fetch_nse_corporate_filings
from src.collectors.bse_filings import fetch_bse_corporate_filings
from src.data_manager import DataManager
from src.pipeline_v3 import run_pipeline_v3


def load_universe(path: str) -> Iterable[Tuple[str, str]]:
    """
    Load the F&O universe from a CSV file.

    Expected columns:
    - symbol: NSE symbol
    - bse_scrip: (optional) BSE scrip code
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Universe file not found: {path}")

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # Handle UTF-8 BOM in the first column name (e.g. '\ufeffsymbol')
        if reader.fieldnames:
            reader.fieldnames = [
                (name.lstrip("\ufeff") if isinstance(name, str) else name)
                for name in reader.fieldnames
            ]

        if "symbol" not in reader.fieldnames:
            raise ValueError(
                f"Universe file {path} must have at least a 'symbol' column, "
                f"found columns: {reader.fieldnames}"
            )

        for row in reader:
            symbol = (row.get("symbol") or "").strip()
            bse_scrip = (row.get("bse_scrip") or "").strip()

            # Skip empty rows
            if not symbol and not bse_scrip:
                continue

            yield symbol, bse_scrip


def display_negative_signals(target_date) -> None:
    """
    Display negative signals from the signals CSV file in a formatted table.
    """
    data_manager = DataManager()
    signals_file = data_manager.get_signals_file(target_date)

    if not signals_file.exists():
        print("\n[Signals] No signals file found.")
        return

    try:
        signals: list = []
        with open(signals_file, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                signals.append(row)

        if not signals:
            print("\n[Signals] No negative signals detected.")
            return

        # Sort by severity_score descending
        signals.sort(
            key=lambda s: float(s.get("severity_score", 0)), reverse=True
        )

        print("\n" + "=" * 120)
        print("NEGATIVE SIGNALS DETECTED")
        print("=" * 120)
        print(
            f"{'SYMBOL':<12} {'EVENT_TYPE':<20} {'IMPACT':<12} {'SEVERITY':<10} {'CONF':<8} {'HEADLINE':<50}"
        )
        print("-" * 120)

        for sig in signals:
            symbol = sig.get("symbol", "-")[:11]
            event_type = sig.get("event_type", "OTHER")[:19]
            impact = sig.get("impact_direction", "NEUTRAL")[:11]
            severity = float(sig.get("severity_score", 0.0))
            conf = float(sig.get("confidence_score", 0.0))
            headline = sig.get("headline", "")[:49]

            print(
                f"{symbol:<12} {event_type:<20} {impact:<12} {severity:<10.2f} {conf:<8.2f} {headline:<50}"
            )

        print("=" * 120)
        print(f"\nTotal negative signals: {len(signals)}")
        print(f"Signals file: {signals_file}")
        
        # Show flag reasons summary
        flag_reasons = {}
        for sig in signals:
            reason = sig.get("flag_reason", "UNKNOWN")
            flag_reasons[reason] = flag_reasons.get(reason, 0) + 1
        
        if flag_reasons:
            print("\nFlag reasons breakdown:")
            for reason, count in sorted(flag_reasons.items(), key=lambda x: x[1], reverse=True):
                print(f"  {reason}: {count}")

    except Exception as exc:  # noqa: BLE001
        print(f"\n[Signals] Error reading signals file: {exc}")


def collect_for_universe(
    universe_path: str, limit: int, parser_version: str = "v3.0"
) -> None:
    """
    Iterate over the F&O universe and collect filings using v3 pipeline.

    Architecture:
    1. Fetch raw articles
    2. Write raw data (never modify)
    3. Enrich → Filter → Classify
    4. Write enriched data and signals
    5. Log execution stats

    Parameters
    ----------
    universe_path : str
        Path to F&O universe CSV
    limit : int
        Max filings per exchange per symbol
    parser_version : str
        Version of parser/enrichment logic
    """
    from datetime import date

    target_date = date.today()
    all_raw_articles: list = []
    total_stats = {
        "raw_items_ingested": 0,
        "raw_items_new": 0,
        "enriched_items_created": 0,
        "routine_filtered": 0,
        "negative_flagged": 0,
        "signals_written": 0,
    }

    # Collect all raw articles first
    for symbol, bse_scrip in load_universe(universe_path):
        print(f"[batch] Processing symbol={symbol or '-'} bse_scrip={bse_scrip or '-'}")

        articles = []

        # NSE filings by symbol
        if symbol:
            try:
                nse_articles = fetch_nse_corporate_filings(symbol, limit=limit)
                print(f"  NSE filings fetched: {len(nse_articles)}")
                articles.extend(nse_articles)
            except Exception as exc:  # noqa: BLE001
                print(f"  Error fetching NSE filings for {symbol}: {exc}")

        # BSE filings by scrip code
        if bse_scrip:
            try:
                bse_articles = fetch_bse_corporate_filings(bse_scrip, limit=limit)
                print(f"  BSE filings fetched: {len(bse_articles)}")
                articles.extend(bse_articles)
            except Exception as exc:  # noqa: BLE001
                print(f"  Error fetching BSE filings for {bse_scrip}: {exc}")

        if articles:
            all_raw_articles.extend(articles)

    # Run pipeline v3 on all collected articles
    if all_raw_articles:
        print(f"\n[Pipeline] Processing {len(all_raw_articles)} total articles...")
        try:
            stats = run_pipeline_v3(
                all_raw_articles, parser_version=parser_version, target_date=target_date
            )
            # Aggregate stats
            for key in total_stats:
                total_stats[key] += stats.get(key, 0)

            print(f"\n[Pipeline] Execution complete:")
            print(f"  Raw items ingested: {stats.get('raw_items_ingested', 0)}")
            print(f"  Raw items new: {stats.get('raw_items_new', 0)}")
            print(f"  Enriched items created: {stats.get('enriched_items_created', 0)}")
            print(f"  Routine filtered: {stats.get('routine_filtered', 0)}")
            print(f"  Negative flagged: {stats.get('negative_flagged', 0)}")
            print(f"  Signals written: {stats.get('signals_written', 0)}")
            print(f"\n[Pipeline] Files written:")
            print(f"  Raw: data/raw/{target_date.isoformat()}/raw_announcements.csv")
            print(f"  Enriched: data/enriched/{target_date.isoformat()}/enriched_events.csv")
            print(f"  Signals: data/signals/{target_date.isoformat()}/negative_signals.csv")
            print(f"  Log: logs/{target_date.isoformat()}/pipeline.log")

            # Display negative signals in terminal
            display_negative_signals(target_date)
        except Exception as exc:  # noqa: BLE001
            print(f"  Error in pipeline: {exc}")
            import traceback

            traceback.print_exc()
    else:
        print("\n[Pipeline] No articles collected.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch collect India F&O filings for derivative-eligible stocks."
    )
    parser.add_argument(
        "--universe",
        default="fo_universe.csv",
        help="Path to F&O universe CSV (default: fo_universe.csv)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Max filings per exchange per symbol (default: 20)",
    )
    parser.add_argument(
        "--parser-version",
        default="v3.0",
        help="Parser/enrichment version (default: v3.0)",
    )
    args = parser.parse_args()

    collect_for_universe(
        args.universe,
        args.limit,
        parser_version=args.parser_version,
    )


if __name__ == "__main__":
    main()


