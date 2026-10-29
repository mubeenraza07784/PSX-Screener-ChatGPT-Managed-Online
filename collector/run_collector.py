#!/usr/bin/env python3
"""Run collector.js in a real browser page on stockanalysis.com and save its output.

This replaces what the Claude scheduled task did with its browser tools
(open a tab, inject collector.js, poll window.MON, read the result).

    python3 collector/run_collector.py --out workdir                 # daily: all ~490 symbols, prices + 1/5 of financials (25-35 min)
    python3 collector/run_collector.py --out workdir --fund-slice 2  # choose which fifth of the financials to refresh (0-4)
    python3 collector/run_collector.py --out workdir --intraday workdir/today.json   # intraday mode, see refresh_intraday.py

Writes <out>/tech_new.txt and (daily mode) <out>/fund_new.txt, the files merge.py reads.

Rules kept from the original bot:
  * requests are paced (700 ms between symbols, in collector.js);
  * on HTTP 429/403 or a "Just a moment" bot check the collector stops fetching (MON.blocked) and
    this script saves whatever was collected – it never retries, solves CAPTCHAs or hides automation;
  * a visible browser with its own profile folder is used. If you choose to sign in to stockanalysis.com
    in that window, the session stays in that profile folder on your computer only; nothing is stored here.
Respect stockanalysis.com's terms of use; this is for personal research.
"""
import argparse, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
START_URL = "https://stockanalysis.com/quote/psx/OGDC/history/"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="folder for tech_new.txt / fund_new.txt (normally workdir)")
    ap.add_argument("--fund-slice", type=int, choices=range(5), help="which fifth of the financials to refresh (default: by weekday)")
    ap.add_argument("--intraday", help="JSON from psx_intraday.py: {todayDate, today:{SYM:[o,h,l,c,v]}, only:[SYM,...]}")
    ap.add_argument("--headless", action="store_true", help="hide the browser (the site may refuse headless browsers)")
    ap.add_argument("--profile", default=os.path.join(os.path.dirname(HERE), ".browser-profile"), help="browser profile folder")
    ap.add_argument("--timeout-min", type=int, default=60)
    a = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("Playwright is not installed: pip install playwright && python -m playwright install chromium")

    opts = {}
    if a.fund_slice is not None:
        opts["fundSlice"] = a.fund_slice
    if a.intraday:
        j = json.load(open(a.intraday))
        opts.update(noFund=True, only=j["only"], todayDate=j["todayDate"], today=j["today"])
    code = open(os.path.join(HERE, "collector.js"), encoding="utf-8").read()
    os.makedirs(a.out, exist_ok=True)

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(a.profile, headless=a.headless)
        page = ctx.new_page()
        page.goto(START_URL, wait_until="domcontentloaded", timeout=60000)
        if "Just a moment" in (page.title() or ""):
            print("stockanalysis.com is showing a bot check. Complete it yourself in the window if you wish, then re-run. Stopping.")
            ctx.close(); sys.exit(2)
        page.evaluate("o => { window.MON_OPTS = o; }", opts)
        page.evaluate(code)  # starts in the background and returns at once
        t0 = time.time(); last = None
        while True:
            time.sleep(20)
            mon = page.evaluate("() => window.MON && {...window.MON}") or {}
            line = f"{mon.get('phase')} {mon.get('done')}/{mon.get('total')} fund {mon.get('fundDone')}/{mon.get('fundTotal')} errors {mon.get('errors')} blocked {mon.get('blocked')}"
            if line != last:
                print(time.strftime("%H:%M:%S"), line, flush=True); last = line
            if mon.get("phase") == "done":
                break
            if time.time() - t0 > a.timeout_min * 60:
                print("timed out waiting for the collector"); ctx.close(); sys.exit(3)
        tech = page.evaluate("() => (window.__TECH || []).join('\\n')")
        fund = page.evaluate("() => (window.__FUND || []).join('\\n')")
        ctx.close()

    n_t = max(0, tech.count("\n")); n_f = max(0, fund.count("\n"))
    open(os.path.join(a.out, "tech_new.txt"), "w", encoding="utf-8").write(tech + "\n")
    if n_f > 0:
        open(os.path.join(a.out, "fund_new.txt"), "w", encoding="utf-8").write(fund + "\n")
    elif os.path.exists(os.path.join(a.out, "fund_new.txt")):
        os.remove(os.path.join(a.out, "fund_new.txt"))
    print(json.dumps({"tech_lines": n_t, "fund_lines": n_f, "blocked": mon.get("blocked"), "errors": mon.get("errors"), "secs": mon.get("secs")}))
    if mon.get("blocked"):
        print("NOTE: the site rate-limited the run; merge.py keeps yesterday's values for symbols not refreshed.")


if __name__ == "__main__":
    main()
