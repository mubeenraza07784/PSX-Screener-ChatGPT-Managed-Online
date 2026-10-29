#!/usr/bin/env python3
"""Write the daily report (the message the Claude monitor sent) as Markdown tables.

    python3 monitor/report.py                     # reads workdir/, prints and saves reports/<date>.md

Sections: (1) alerts today, holdings/watchlist first; (2) holdings check; (3) Strategy 1-9 lists, with
Strategy 6 setups and the KSE-100 proxy Alligator; (4) data coverage.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, "workdir")
HOLD = ['ABOT', 'COLG', 'DCR', 'ENGROH', 'FFC', 'HUBC', 'LUCK', 'MARI', 'MEBL', 'MTL', 'OGDC']  # keep in sync with engine/analyze.py
WATCH = ['SAZEW', 'GHNI']


def fmt(v, d=2):
    if v is None or v == "":
        return "–"
    if isinstance(v, (int, float)):
        return f"{v:,.0f}" if abs(v) >= 1000 else f"{v:,.{d}f}"
    return str(v)


def table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    out += ["| " + " | ".join(str(c).replace("|", "/") for c in r) + " |" for r in rows]
    return "\n".join(out)


def main(coverage_note=""):
    ds = os.path.join(W, "ds")
    strat = json.load(open(os.path.join(ds, "strategies.json")))
    rules = {r["strategy"]: r for r in json.load(open(os.path.join(ds, "strategy_rules.json")))}
    market = json.load(open(os.path.join(ds, "market.json")))[0]
    summary = open(os.path.join(W, "summary.txt")).read() if os.path.exists(os.path.join(W, "summary.txt")) else ""
    asof = market["as_of"]
    md = [f"# PSX monitor – {asof}", ""]

    # 1) alerts
    lines = [l for l in summary.splitlines()[1:] if ":" in l]
    rows = []
    for l in lines:
        sym, rest = l.split(":", 1)
        typ, _, det = rest.strip().partition(" – ")
        tag = " (you hold)" if sym in HOLD else " (watchlist)" if sym in WATCH else ""
        rows.append((0 if tag == " (you hold)" else 1 if tag else 2, [sym + tag, typ, det]))
    rows.sort(key=lambda x: x[0])
    md += ["## 1. Alerts today", table(["Symbol", "Alert", "Detail"], [r for _, r in rows]) if rows else "No new signals today.", ""]
    if summary and len(summary.splitlines()) > 13:
        md.append("_Only the first 12 alerts are in summary.txt; the full list is in workdir/alerts_history.json._\n")

    # 2) holdings check
    sh = [r for r in strat if r["strategy"] == "SH"]
    md += ["## 2. Holdings check", rules.get("SH", {}).get("rule", ""), "",
           table(["Symbol", "Group", "Price", "Intrinsic value", "MOS %", "Score", "Check"],
                 [[r["sym"], r.get("group") or "", fmt(r["price"]), fmt(r.get("iv"), 1), fmt(r.get("mos"), 0), fmt(r.get("fund_score"), 1), r.get("review") or ""] for r in sh]), ""]

    # 3) strategies
    md.append("## 3. Strategy lists")
    for sid in ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9"]:
        picks = [r for r in strat if r["strategy"] == sid]
        if sid not in rules:
            continue
        md.append(f"**{rules[sid]['strategy_name']}** ({len(picks)}): " + (", ".join(r["sym"] for r in picks) or "none today"))
    s6 = [r for r in strat if r["strategy"] == "S6"]
    if s6:
        md += ["", "Strategy 6 setups (course rules, 1:3 target):",
               table(["Symbol", "Setup", "Entry", "Stop", "Target", "Qty for 1% risk"],
                     [[r["sym"], r.get("setup") or "", fmt(r.get("entry")), fmt(r.get("stop")), fmt(r.get("target")), fmt(r.get("qty_for_risk"), 0)] for r in s6])]
        m = re.search(r"Alligator: daily (\w+), weekly (\w+)", rules["S6"]["rule"])
        if m:
            md.append(f"\nKSE-100 proxy Alligator: daily **{m.group(1)}**, weekly **{m.group(2)}** (the course takes buy setups only when the index is bullish).")
    md += ["", f"Strong candidates: **{market['strong_candidates']}** · Strong fundamentals – wait for setup: {market['strong_wait']} · Avoid: {market['avoid']}", ""]

    # 4) coverage
    md += ["## 4. Data coverage",
           table(["PSX symbols", "Analysed", "With financials", "Rated (liquid)", "KSE-100 median P/E", "Above 200-DMA"],
                 [[market["psx_symbols"], market["analysed"], market["with_fundamentals"], market["rated_liquid"], market["kse100_median_pe"], f"{market['pct_above_200dma']}%"]])]
    if coverage_note:
        md.append(coverage_note)
    md += ["", "Signals apply your course rules mechanically; not investment advice."]
    text = "\n".join(md) + "\n"
    os.makedirs(os.path.join(ROOT, "reports"), exist_ok=True)
    fn = os.path.join(ROOT, "reports", f"{asof}.md")
    open(fn, "w", encoding="utf-8").write(text)
    print(text)
    print(f"(saved {fn})")


if __name__ == "__main__":
    main(" ".join(sys.argv[1:]))
