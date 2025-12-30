"""
NSE corporate filings collector.

Fetches recent corporate announcements for a given NSE symbol
using NSE's public corporate-announcements API.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

import requests

_BASE_URL = "https://www.nseindia.com"
_ANNOUNCEMENTS_URL = _BASE_URL + "/api/corporate-announcements"

_session = requests.Session()
_session.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Referer": _BASE_URL + "/",
    }
)


def _init_session() -> None:
    """Warm up session so NSE sets cookies.

    NSE sometimes returns 403 for scripted clients even on the homepage.
    We treat a 403 here as non-fatal and still attempt the API call.
    """
    try:
        resp = _session.get(_BASE_URL, timeout=10)
        # If homepage is forbidden, just continue – API might still work.
        if resp.status_code == 403:
            return
        resp.raise_for_status()
    except requests.RequestException:
        # Network or other HTTP errors in warm-up are non-fatal.
        return


def fetch_nse_corporate_filings(symbol: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Fetch recent NSE corporate filings for a given symbol.

    Parameters
    ----------
    symbol : str
        NSE ticker symbol (e.g. 'RELIANCE').
    limit : int, optional
        Maximum number of filings to return.

    Returns
    -------
    List[Dict[str, Any]]
        List of article/filing dicts consumed by the pipeline.
    """
    if not symbol:
        return []

    # Query the last 7 days of announcements
    to_date = datetime.now()
    from_date = to_date - timedelta(days=7)

    params = {
        "index": "equities",
        "symbol": symbol,
        "from_date": from_date.strftime("%d-%m-%Y"),
        "to_date": to_date.strftime("%d-%m-%Y"),
    }

    # Ensure we have cookies
    _init_session()

    resp = _session.get(_ANNOUNCEMENTS_URL, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    # NSE may return either a dict {"data": [...]} or a bare list [...]
    if isinstance(data, dict):
        rows = data.get("data") or data.get("items") or []
    elif isinstance(data, list):
        rows = data
    else:
        rows = []
    articles: List[Dict[str, Any]] = []

    for row in rows[:limit]:
        headline = row.get("sm_desc", "") or row.get("desc", "")
        dt = row.get("datetime") or row.get("broadcastDate") or ""
        source = "NSE_CORP_ANN"
        # Extract NSE category (common field names)
        nse_category = (
            row.get("category")
            or row.get("subCategoryName")
            or row.get("sub_category")
            or row.get("announcementCategory")
            or ""
        )

        article = {
            "symbol": symbol,
            "source": source,
            "headline": headline,
            "summary": row.get("attchmntText", "") or "",
            "published_at": dt,
            "nse_category": nse_category,  # Add category for enrichment
            "raw": row,
            "score": 0.0,  # your pipeline can set real scores later
        }
        articles.append(article)

        # Lightweight debug so you can see what is fetched in the console
        print(f"[NSE] {symbol} {dt} - {headline}")

    return articles



