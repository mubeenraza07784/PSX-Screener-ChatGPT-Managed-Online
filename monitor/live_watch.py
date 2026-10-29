#!/usr/bin/env python3
"""Hourly live watch during market hours (08:33–15:33 PKT in the original) for holdings, watchlist and Strategy 6.

    python3 monitor/live_watch.py                         # fetch latest trades (browser) and check levels
    python3 monitor/live_watch.py --ticks ticks.json      # check levels against ticks you already have

Rules (from the Claude "PSX live watch" task), per symbol in workdir/live_watch.json, with latest price P,
today's high H and low L; each alert key (SYM:type) fires once a day (workdir/live_state.json):
  entry and H >= entry   -> "Buy-stop level reached"
  stop  and L <= stop    -> "Stop level hit"
  target and H >= target -> "1:3 target reached"
  jaw: close_prev < jaw < P -> "Price back above the daily Jaw (CWT Scenario 2 condition – confirm on your 4H chart)"
       close_prev > jaw > P -> "Price fell below the daily Jaw"
  |P/close_prev - 1| >= 5%  -> "Big move today", and >= 10% (circuit) as a separate key
Prints a Markdown table (holdings first) only when there is something new.
"""
import argparse, datetime as dt, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, "workdir")
ORDER = {"holding": 0, "watchlist": 1, "strategy6": 2}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticks", help="JSON with a 'ticks' object {SYM:[time,last,high,low]} (from psx_intraday.py)")
    ap.add_argument("--headless", action="store_true")
    a = ap.parse_args()
    lw = json.load(open(os.path.join(W, "live_watch.json")))
    stp = os.path.join(W, "live_state.json")
    st = json.load(open(stp)) if os.path.exists(stp) else {"date": "", "fired": []}
    today = dt.datetime.now(dt.timezone(dt.timedelta(hours=5))).date().isoformat()
    fired = set(st["fired"]) if st.get("date") == today else set()

    tick_file = a.ticks
    if not tick_file:
        tick_file = os.path.join(W, "ticks.json")
        cmd = [sys.executable, os.path.join(ROOT, "collector", "psx_intraday.py"), "--syms-from", os.path.join(W, "live_watch.json"), "--watch", "--out", tick_file]
        if a.headless: cmd.append("--headless")
        if subprocess.run(cmd).returncode != 0:
            sys.exit("could not read PSX prices")
    ticks = json.load(open(tick_file))["ticks"]

    new = []
    for s in lw["symbols"]:
        t = ticks.get(s["sym"])
        if not t:
            continue
        _, P, H, L = t
        cp = s.get("close_prev")
        def fire(kind, text, level):
            key = f"{s['sym']}:{kind}"
            if key not in fired:
                fired.add(key); new.append((ORDER.get(s["group"], 3), [s["sym"], s["group"], text, f"{P:,.2f}", level]))
        if s.get("entry") and H >= s["entry"]:
            fire("entry", f"Buy-stop level reached ({s.get('setup')}); stop {s.get('stop')}, target {s.get('target')}", f"{s['entry']:,.2f}")
        if s.get("stop") and L <= s["stop"]:
            fire("stop", "Stop level hit", f"{s['stop']:,.2f}")
        if s.get("target") and H >= s["target"]:
            fire("target", "1:3 target reached", f"{s['target']:,.2f}")
        jaw = s.get("jaw")
        if jaw and cp:
            if cp < jaw < P:
                fire("jaw_up", "Price back above the daily Jaw (CWT Scenario 2 condition – confirm on your 4H chart)", f"{jaw:,.2f}")
            if cp > jaw > P:
                fire("jaw_down", "Price fell below the daily Jaw", f"{jaw:,.2f}")
        if cp:
            ch = (P / cp - 1) * 100
            if abs(ch) >= 5:
                fire("move5", f"Big move today ({ch:+.1f}%)", f"{cp:,.2f} prev close")
            if abs(ch) >= 10:
                fire("move10", f"Circuit-size move today ({ch:+.1f}%)", f"{cp:,.2f} prev close")
    if not new:
        print("no new alerts"); return
    new.sort(key=lambda x: x[0])
    print("| Symbol | Group | Alert | Price | Level |\n|---|---|---|---|---|")
    for _, r in new:
        print("| " + " | ".join(r) + " |")
    k = ticks.get("KSE100")
    if k:
        print(f"\nKSE-100 latest {k[1]:,.2f} (day high {k[2]:,.2f}, low {k[3]:,.2f}).")
    print("\nLevels are from your course rules on last close; confirm on your 4H chart. Not investment advice.")
    json.dump({"date": today, "fired": sorted(fired)}, open(stp, "w"))


if __name__ == "__main__":
    main()
