from datetime import datetime, timedelta

from src.pipeline import run_pipeline


now = datetime.utcnow()


def mk_article(symbol, headline, body, days_ago, source="NSE"):
    ts = now - timedelta(days=days_ago)
    return {
        "symbol": symbol,
        "source": source,
        "headline": headline,
        "body": body,
        "published_at": ts.isoformat(),
    }


articles = [
    # Routine filing → should be filtered out
    mk_article("TEST", "Outcome of board meeting", "", 1, "NSE"),
    mk_article("TEST2", "Board meeting intimation", "", 1, "BSE"),
    # RBI penalty → signal
    mk_article("BANKX", "RBI imposes monetary penalty on BANKX", "", 1, "RBI"),
    # Guidance cut → strong signal
    mk_article("COFX", "Company COFX cuts earnings guidance", "", 0, "Moneycontrol"),
    # Rating downgrade → strong signal
    mk_article("RATEX", "Rating downgraded by CRISIL", "", 0, "Economic Times"),
]


if __name__ == "__main__":
    signals = run_pipeline(articles, context_enabled=False)
    for s in signals:
        print(s)


























