#!/usr/bin/env python3
"""Daily after-close refresh – the same steps the Claude "PSX screener daily monitor" task ran at 5:43 pm PKT.

    python3 monitor/refresh_daily.py                  # collect (25-35 min) -> merge -> analyze -> alerts -> build -> report
    python3 monitor/refresh_daily.py --skip-collect   # recompute from the saved state only (no internet)
    python3 monitor/refresh_daily.py --fixed-alerts   # use engine/alerts_v2.py instead of alerts.py (see docs/KNOWN_ISSUES.md)
    python3 monitor/refresh_daily.py --weekly         # also rebuild psx_meta.txt from the PSX screener (Mondays in the original)

Afterwards: data/current/*.json, dashboard/standalone.html and reports/<date>.md are updated.
Macro readings (workdir/macro_src.json) and the T-bill/policy rate (workdir/config.json) are edited by hand;
the original bot refreshed them by web search on Mondays (see docs/ECONOMY_UPDATE.md).
"""
import argparse, glob, os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, "workdir")
E = os.path.join(ROOT, "engine")
PY = sys.executable


def run(args, cwd=ROOT):
    print("$", " ".join(os.path.relpath(a, ROOT) if os.path.isabs(a) else a for a in args), flush=True)
    r = subprocess.run(args, cwd=cwd)
    if r.returncode != 0:
        sys.exit(f"step failed ({r.returncode}): {' '.join(args)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-collect", action="store_true")
    ap.add_argument("--fixed-alerts", action="store_true")
    ap.add_argument("--weekly", action="store_true")
    ap.add_argument("--headless", action="store_true")
    a = ap.parse_args()
    hl = ["--headless"] if a.headless else []

    for f in ("tech_new.txt", "fund_new.txt"):
        if os.path.exists(os.path.join(W, f)):
            os.remove(os.path.join(W, f))
    note = ""
    if not a.skip_collect:
        if a.weekly:
            run([PY, os.path.join(ROOT, "collector", "psx_screener_meta.py"), "--out", os.path.join(W, "psx_meta.txt")] + hl)
        run([PY, os.path.join(ROOT, "collector", "run_collector.py"), "--out", W] + hl)
        new = [f for f in ("tech_new.txt", "fund_new.txt") if os.path.exists(os.path.join(W, f))]
        if new:
            run([PY, os.path.join(E, "merge.py")] + new, cwd=W)
    run([PY, os.path.join(E, "analyze.py")], cwd=W)
    run([PY, os.path.join(E, "alerts_v2.py" if a.fixed_alerts else "alerts.py")], cwd=W)
    run([PY, os.path.join(E, "build_ds.py")], cwd=W)
    size = os.path.getsize(os.path.join(W, "features.txt"))
    if size > 250_000:
        note = f"Note: features.txt is {size/1000:.0f} KB (the Claude store limit was 256 KB; irrelevant outside Claude)."

    out = os.path.join(ROOT, "data", "current")
    os.makedirs(out, exist_ok=True)
    for f in glob.glob(os.path.join(W, "ds", "*.json")):
        shutil.copy(f, out)
    run([PY, os.path.join(ROOT, "dashboard", "build_standalone.py")])
    run([PY, os.path.join(ROOT, "monitor", "report.py")] + ([note] if note else []))


if __name__ == "__main__":
    main()
