#!/usr/bin/env python3
"""Today's running candle / latest trade for a list of symbols from the PSX data portal.

Replaces step 3 of the Claude "intraday refresh" and "live watch" tasks.
The portal's /timeseries/int/<SYM> endpoint only answers requests made by its own page
(through jQuery), so this opens https://dps.psx.com.pk/company/OGDC in a browser and calls
jQuery.ajax from inside that page, 6 symbols at a time.

    python3 collector/psx_intraday.py --syms-from workdir/live_watch.json --out workdir/today.json
    python3 collector/psx_intraday.py --syms ABOT,FFC,KSE100 --out ticks.json

Output JSON:
  {"todayDate": "YYYY-MM-DD", "only": [...symbols...],
   "today": {SYM: [open, high, low, close, volume]},        # for run_collector.py --intraday
   "ticks": {SYM: [lastTradeUnixTime, last, dayHigh, dayLow]}}  # for monitor/live_watch.py
Each portal response is [[unixTime, price, volume], ...] newest first:
open = price of the LAST element, high/low = max/min price, close = data[0][1], volume = sum.
If the page refuses (bot check / 403) the script stops; it never works around it.
"""
import argparse, datetime as dt, json, os, sys

JS = r"""
async (syms) => {
  if (!window.jQuery) return {error: 'jQuery not on page'};
  const out = {today: {}, ticks: {}, failed: []};
  const one = (s) => new Promise((res) => {
    jQuery.ajax({url: '/timeseries/int/' + s, timeout: 15000})
      .done((r) => {
        const d = (r && r.data) || [];
        if (!d.length) { out.failed.push(s); return res(); }
        let hi = -Infinity, lo = Infinity, vol = 0;
        for (const x of d) { hi = Math.max(hi, +x[1]); lo = Math.min(lo, +x[1]); vol += +(x[2] || 0); }
        out.today[s] = [+d[d.length - 1][1], hi, lo, +d[0][1], vol];
        out.ticks[s] = [+d[0][0], +d[0][1], hi, lo];
        res();
      })
      .fail(() => { out.failed.push(s); res(); });
  });
  for (let i = 0; i < syms.length; i += 6) await Promise.all(syms.slice(i, i + 6).map(one));
  return out;
}
"""


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--syms", help="comma-separated symbols")
    g.add_argument("--syms-from", help="live_watch.json: uses intraday_syms, or the watch symbols with --watch")
    ap.add_argument("--watch", action="store_true", help="with --syms-from: the ~21 watched symbols + KSE100 (live watch)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--profile", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".browser-profile"))
    a = ap.parse_args()
    if a.syms:
        syms = [s.strip().upper() for s in a.syms.split(",") if s.strip()]
    else:
        lw = json.load(open(a.syms_from))
        syms = [x["sym"] for x in lw["symbols"]] + ["KSE100"] if a.watch else lw["intraday_syms"]
    syms = list(dict.fromkeys(syms))

    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(a.profile, headless=a.headless)
        page = ctx.new_page()
        resp = page.goto("https://dps.psx.com.pk/company/OGDC", wait_until="domcontentloaded", timeout=60000)
        if resp and resp.status in (403, 429):
            sys.exit(f"PSX portal answered {resp.status}; stopping.")
        page.wait_for_function("() => !!window.jQuery", timeout=30000)
        res = page.evaluate(JS, syms)
        ctx.close()
    if res.get("error"):
        sys.exit(res["error"])
    today = dt.datetime.now(dt.timezone(dt.timedelta(hours=5))).date().isoformat()  # PKT
    out = {"todayDate": today, "only": [s for s in syms if s in res["today"] and s != "KSE100"], "today": res["today"], "ticks": res["ticks"], "failed": res["failed"]}
    json.dump(out, open(a.out, "w"), indent=0)
    print(f"{len(res['today'])} symbols, {len(res['failed'])} failed -> {a.out}")


if __name__ == "__main__":
    main()
