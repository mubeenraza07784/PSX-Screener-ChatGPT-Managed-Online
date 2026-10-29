#!/usr/bin/env python3
"""Import an authorized *complete technical-feature* snapshot, never scrape a website.

Accepts the same pipe-delimited TECHF/COTURSEF output the exported scoring engine
already knows how to merge. Raw closing prices alone are not sufficient: using
old RSI/MACD/CWT signals with new prices would produce misleading signals.

Run locally or through the manual GitHub Actions refresh workflow. The import
pre-validates all source rows before touching the existing saved state.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import re
import subprocess
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_TECH = set("""sym P s20 s50 s200 rsi macdH macdX r1m r3m r6m r1y hi lo vol beta
trend sup res fibLeg fibR cds vR val lastDate allD allW cwt mtf haLips jaw dow
swH frL div fvgB flip pats patN patD patK patS patE patSL patT mktD mktW""".split())
SYMBOL = re.compile(r"^[A-Z][A-Z0-9]{0,11}$")


def read_pipe(path: Path, required: set[str]) -> list[dict[str, str]]:
    if not path.is_file():
        raise ValueError(f"Missing source file: {path}")
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    if not lines:
        raise ValueError("Empty source file")
    header = lines[0].split("|")
    if len(header) != len(set(header)) or not required.issubset(header):
        missing = sorted(required - set(header))
        raise ValueError(f"Invalid source header; missing columns: {missing}; duplicate columns: {len(header) != len(set(header))}")
    rows = []
    seen = set()
    for n, line in enumerate(lines[1:], 2):
        if not line.strip():
            continue
        fields = line.split("|")
        if len(fields) != len(header):
            raise ValueError(f"Line {n}: expected {len(header)} columns, got {len(fields)}")
        record = dict(zip(header, fields))
        symbol = record["sym"].strip()
        if not SYMBOL.fullmatch(symbol) or symbol in seen:
            raise ValueError(f"Line {n}: duplicate or invalid symbol {symbol!r}")
        seen.add(symbol)
        rows.append(record)
    return rows


def validate(tech: Path, manifest_path: Path, known_symbols: set[str], today: dt.date) -> tuple[int, str]:
    if not manifest_path.is_file():
        raise ValueError("Missing imports/source.json. See imports/README.md")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("permission_confirmed") is not True or not str(manifest.get("provider", "")).strip() or not str(manifest.get("permission_basis", "")).strip():
        raise ValueError("Record a real provider and permission basis, and confirm permission in source.json. This is an attestation, not automated license verification.")
    source_date = dt.date.fromisoformat(manifest["as_of"])
    if source_date != today:
        raise ValueError(f"Refusing stale/future import: source date {source_date}, PKT date {today}")
    rows = read_pipe(tech, REQUIRED_TECH)
    minimum = max(400, math.ceil(0.85 * len(known_symbols)))
    if len(rows) < minimum:
        raise ValueError(f"Only {len(rows)} symbols; at least {minimum} required for safe full-screener refresh")
    for row in rows:
        symbol = row["sym"]
        if symbol not in known_symbols:
            raise ValueError(f"Unknown symbol {symbol}; update PSX metadata through a verified feed first")
        if row["lastDate"] != source_date.isoformat():
            raise ValueError(f"{symbol}: row date {row['lastDate']!r} differs from {source_date}")
        try:
            price = float(row["P"])
        except ValueError:
            raise ValueError(f"{symbol}: missing or nonnumeric close") from None
        if not math.isfinite(price) or price <= 0:
            raise ValueError(f"{symbol}: invalid close {price}")
        for field in ("rsi", "s20", "s50", "s200", "macdH"):
            if row[field].strip():
                try:
                    val = float(row[field])
                except ValueError:
                    raise ValueError(f"{symbol}: invalid {field}") from None
                if not math.isfinite(val) or (field == "rsi" and not 0 <= val <= 100):
                    raise ValueError(f"{symbol}: out-of-range {field}")
    return len(rows), source_date.isoformat()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tech", type=Path, default=ROOT / "imports" / "tech_new.txt")
    parser.add_argument("--fund", type=Path, default=ROOT / "imports" / "fund_new.txt")
    parser.add_argument("--manifest", type=Path, default=ROOT / "imports" / "source.json")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    header = (ROOT / "workdir" / "features.txt").read_text(encoding="utf-8").splitlines()[0].split("|")
    ix = header.index("sym")
    known = {r.split("|")[ix] for r in (ROOT / "workdir" / "features.txt").read_text(encoding="utf-8").splitlines()[1:] if r.strip()}
    today = dt.datetime.now(ZoneInfo("Asia/Karachi")).date()
    try:
        count, date = validate(args.tech, args.manifest, known, today)
        if args.fund.is_file():
            funds = read_pipe(args.fund, {"sym", "fy", "epsT"})
            if any(r["sym"] not in known for r in funds):
                raise ValueError("Fundamentals contain unknown symbols")
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        sys.exit(f"IMPORT REJECTED: {exc}")
    print(f"Validated {count} complete technical feature rows for {date}; source authorization was self-attested.", flush=True)
    if args.check_only:
        return
    cmd = [sys.executable, str(ROOT / "engine" / "merge.py"), str(args.tech.resolve())]
    if args.fund.is_file():
        cmd.append(str(args.fund.resolve()))
    subprocess.run(cmd, cwd=ROOT / "workdir", check=True)
    subprocess.run([sys.executable, str(ROOT / "monitor" / "refresh_daily.py"), "--skip-collect", "--fixed-alerts"], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / "cloud" / "verify_freshness.py")], cwd=ROOT, check=True)
    print("Approved-source refresh completed. The current-date validation does not independently certify data accuracy or source rights.")


if __name__ == "__main__":
    main()
