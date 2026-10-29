#!/usr/bin/env python3
"""Hourly intraday refresh (10:07–15:07 PKT in the original) – recompute the dashboard with today's running candle.

    python3 monitor/refresh_intraday.py

Steps (as in the Claude "PSX dashboard intraday refresh (hourly)" task):
 1. today's candles for live_watch.json's ~190 intraday_syms from the PSX data portal (collector/psx_intraday.py)
 2. collector.js in intraday mode (prices only, today's candle appended) on stockanalysis.com (~3 min)
 3. merge -> analyze -> build_ds in a TEMPORARY copy of workdir: alerts.py is NOT run and the saved state
    (features.txt, last_signals.json, alerts_history.json) is NOT changed – the evening run keeps the official history
 4. data/current/*.json + dashboard rebuilt (today's candle is not final)
"""
import datetime as dt, glob, os, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, "workdir")
E = os.path.join(ROOT, "engine")
PY = sys.executable


def run(args, cwd=ROOT):
    print("$", " ".join(args), flush=True)
    if subprocess.run(args, cwd=cwd).returncode != 0:
        sys.exit("step failed: " + " ".join(args))


def main():
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=5)))
    if now.weekday() >= 5 or not (dt.time(9, 45) <= now.time() <= dt.time(16, 0)):
        if "--force" not in sys.argv:
            print("outside PSX hours (Mon–Fri 09:45–16:00 PKT); use --force to run anyway"); return
    hl = ["--headless"] if "--headless" in sys.argv else []
    tmp = tempfile.mkdtemp(prefix="psx_intraday_")
    for f in glob.glob(os.path.join(W, "*")):
        if os.path.isfile(f):
            shutil.copy(f, tmp)
    today = os.path.join(tmp, "today.json")
    run([PY, os.path.join(ROOT, "collector", "psx_intraday.py"), "--syms-from", os.path.join(W, "live_watch.json"), "--out", today] + hl)
    run([PY, os.path.join(ROOT, "collector", "run_collector.py"), "--out", tmp, "--intraday", today] + hl)
    run([PY, os.path.join(E, "merge.py"), "tech_new.txt"], cwd=tmp)
    run([PY, os.path.join(E, "analyze.py")], cwd=tmp)
    run([PY, os.path.join(E, "build_ds.py")], cwd=tmp)
    out = os.path.join(ROOT, "data", "current")
    for f in ("stocks", "strategies", "strategy_rules", "sectors", "market"):
        shutil.copy(os.path.join(tmp, "ds", f + ".json"), out)
    run([PY, os.path.join(ROOT, "dashboard", "build_standalone.py")])
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"intraday refresh {now:%H:%M} PKT done (today's candle not final)")


if __name__ == "__main__":
    main()
