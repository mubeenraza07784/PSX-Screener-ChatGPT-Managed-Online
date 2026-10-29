#!/usr/bin/env python3
"""Fail closed if collection produced too little data or data isn't today's PSX session.

Used by the optional cloud refresh workflow to prevent old data from being
committed as a fresh daily update. Does not defeat source rate limits.
"""
from __future__ import annotations

import datetime as dt
import json
from collections import Counter
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
TODAY = dt.datetime.now(ZoneInfo("Asia/Karachi")).date().isoformat()
STOCKS = json.loads((ROOT / "data/current/stocks.json").read_text())
MARKET = json.loads((ROOT / "data/current/market.json").read_text())
COUNTS = Counter(str(s.get("last_price_date", "")) for s in STOCKS)
LATEST_COUNT = COUNTS.get(TODAY, 0)
MARKET_DATE = str(MARKET[0].get("as_of", "")) if MARKET else ""
MIN_FRESH = 300
print(f"PSX today={TODAY}; market as_of={MARKET_DATE}; same-day companies={LATEST_COUNT}; total companies={len(STOCKS)}")
if MARKET_DATE != TODAY or LATEST_COUNT < MIN_FRESH:
    raise SystemExit(
        f"REFRESH REJECTED: needs same-day market date and >= {MIN_FRESH} same-day stock prices. "
        "Likely source block, partial collection, holiday, or stale feed. Old published data must remain untouched."
    )
print("Freshness gate passed; not a guarantee that every indicator, fundamental metric, or symbol is current.")
