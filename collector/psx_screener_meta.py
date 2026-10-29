#!/usr/bin/env python3
"""Weekly: rebuild workdir/psx_meta.txt (sector, index membership, P/E, DY, free float, volume) from
the PSX data portal screener (https://dps.psx.com.pk/screener).

Line format (what analyze.py reads):
    BASE|PSXSYM|SECTORCODE|FLAGS|PRICE|PE|DY|FREEFLOAT|VOL30
  BASE      symbol without a trailing XD/XR/XB/NC
  FLAGS     three digits: KSE-100 member, KSE-30 member, KMI/Shariah member (from the "LISTED IN" column)
  numbers   plain, no thousands commas

NOTE: in Claude this step was done by an instruction, not saved code, so this script maps the screener's
columns by their header text. Check the "columns found" line on the first run; if PSX renames a column,
adjust COLS below. The file is only overwritten when 700+ rows are parsed.

    python3 collector/psx_screener_meta.py --out workdir/psx_meta.txt
"""
import argparse, os, re, sys

COLS = {  # our field -> header text candidates (lower case, matched by "contains")
    "sym": ["symbol"], "sector": ["sector"], "listed": ["listed in", "listed"], "price": ["price", "current"],
    "pe": ["p/e", "pe ratio", "pe"], "dy": ["dividend yield", "div. yield", "yield"], "ff": ["free float", "freefloat"],
    "vol": ["30 day", "avg. volume", "average volume", "volume"],
}

JS = r"""
async () => {
  const t = await fetch('/screener').then(r => r.text());
  const d = new DOMParser().parseFromString(t, 'text/html');
  const tb = d.querySelector('table'); if (!tb) return {error: 'no table'};
  const heads = [...tb.querySelectorAll('thead th')].map(x => x.textContent.trim());
  const rows = [...tb.querySelectorAll('tbody tr')].map(tr => {
    const td = [...tr.querySelectorAll('td')];
    return td.map(x => ({text: x.textContent.trim(), sector: x.getAttribute('data-sector') || x.getAttribute('data-value') || ''}));
  });
  // sector names -> codes from the page's own filter list
  const live = document;
  const secOpts = Object.fromEntries([...live.querySelectorAll('select[name=sector] option')].map(o => [o.textContent.trim().toLowerCase(), o.value]));
  return {heads, rows, secOpts};
}
"""


def num(s):
    s = (s or "").replace(",", "").replace("%", "").strip()
    try:
        float(s); return s
    except ValueError:
        return "0.00" if s in ("", "-", "N/A") else s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--profile", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".browser-profile"))
    a = ap.parse_args()
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(a.profile, headless=a.headless)
        page = ctx.new_page()
        resp = page.goto("https://dps.psx.com.pk/screener", wait_until="domcontentloaded", timeout=60000)
        if resp and resp.status in (403, 429):
            sys.exit(f"PSX portal answered {resp.status}; stopping.")
        res = page.evaluate(JS)
        ctx.close()
    if res.get("error"):
        sys.exit(res["error"])
    heads = [h.lower() for h in res["heads"]]
    idx = {}
    for k, cands in COLS.items():
        for c in cands:
            hit = [i for i, h in enumerate(heads) if c in h and i not in idx.values()]
            if hit:
                idx[k] = hit[0]; break
    print("columns found:", {k: res["heads"][i] for k, i in idx.items()})
    missing = [k for k in ("sym", "sector", "listed", "price") if k not in idx]
    if missing:
        sys.exit(f"could not find columns {missing} in {res['heads']}; edit COLS")
    sec = res["secOpts"]
    out = []
    for r in res["rows"]:
        g = lambda k: r[idx[k]]["text"] if k in idx and idx[k] < len(r) else ""
        psym = g("sym")
        if not psym:
            continue
        base = re.sub(r"(XD|XR|XB|NC)$", "", psym)
        s_txt = g("sector"); code = r[idx["sector"]]["sector"] or sec.get(s_txt.lower(), s_txt)
        L = g("listed").upper()
        flags = ("1" if "KSE100" in L.replace("-", "").replace(" ", "") else "0") + \
                ("1" if "KSE30" in L.replace("-", "").replace(" ", "") else "0") + \
                ("1" if "KMI" in L else "0")
        out.append("|".join([base, psym, code, flags, num(g("price")), num(g("pe")), num(g("dy")), g("ff").replace(",", ""), g("vol").replace(",", "")]))
    print(f"{len(out)} rows parsed")
    if len(out) < 700:
        sys.exit("fewer than 700 rows – not overwriting psx_meta.txt")
    open(a.out, "w").write("\n".join(out) + "\n")
    print("wrote", a.out)


if __name__ == "__main__":
    main()
