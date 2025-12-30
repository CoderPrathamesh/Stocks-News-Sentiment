import sqlite3


def main() -> None:
    conn = sqlite3.connect("signals.db")
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, symbol, headline, score, published_at
        FROM signals
        ORDER BY id DESC
        LIMIT 50
        """
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        print("No signals stored yet.")
        return

    for row in rows:
        _id, symbol, headline, score, ts = row
        print(f"[{_id}] {symbol} score={score:.2f} at {ts}")
        print(f"  {headline}")


if __name__ == "__main__":
    main()


























