#!/usr/bin/env python3
"""Build the standalone dashboard from the original Claude page + the latest data.

    python3 dashboard/build_standalone.py            # uses data/current/*.json
    python3 dashboard/build_standalone.py --data data/published_snapshot

Writes:
  dashboard/data.js                      window.PSX_DATA = {...}
  dashboard/standalone.html              page + theme + d3 + shim, loads data.js (open it in a browser)
  dashboard/psx-screener-single-file.html  everything inlined into one file (easy to share / upload)

The original page (index.original.html) is NOT edited. Its <script> blocks are wrapped in
an IIFE each, because the Claude runtime runs every script in its own scope (two scripts both
declare `const PX`), while a normal browser page shares one global scope.
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATASETS = ["stocks", "strategies", "strategy_rules", "sectors", "market", "alerts", "macro", "criteria"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.join(ROOT, "data", "current"), help="folder with the 8 dataset JSON files")
    a = ap.parse_args()

    data = {}
    for ds in DATASETS:
        fn = os.path.join(a.data, ds + ".json")
        if not os.path.exists(fn):
            sys.exit(f"missing {fn} – run the pipeline (monitor/refresh_daily.py) or point --data at a folder that has it")
        data[ds] = json.load(open(fn, encoding="utf-8"))
    data_js = "window.PSX_DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n"
    open(os.path.join(HERE, "data.js"), "w", encoding="utf-8").write(data_js)

    page = open(os.path.join(HERE, "index.original.html"), encoding="utf-8").read()
    page = page.replace('<meta name="dash-one-writer">', "", 1)
    # wrap each inline script in its own scope, as the Claude runtime does
    page = re.sub(r"<script>(.*?)</script>", lambda m: "<script>(function(){\n" + m.group(1) + "\n})();</script>", page, flags=re.S)

    as_of = (data["market"][0].get("as_of") if data["market"] else "") or ""
    banner = (f'<div class="export-banner">PSX strategy screener · standalone export · data as of {as_of} · '
              'signals apply the course rules mechanically; not investment advice</div>')

    def doc(head_assets, tail_assets):
        return ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
                "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
                "<title>PSX strategy screener</title>\n" + head_assets + "\n</head>\n<body>\n" + banner +
                "\n<div id=\"dash-root\">\n" + page + "\n</div>\n" + tail_assets + "\n</body>\n</html>\n")

    linked = doc('<link rel="stylesheet" href="theme.css">\n<script src="vendor/d3.v7.9.0.min.js"></script>\n'
                 '<script src="data.js"></script>\n<script src="dash-shim.js"></script>',
                 "<script>window.DASH_SHIM_START();</script>")
    open(os.path.join(HERE, "standalone.html"), "w", encoding="utf-8").write(linked)

    rd = lambda f: open(os.path.join(HERE, f), encoding="utf-8").read()
    single = doc("<style>\n" + rd("theme.css") + "\n</style>\n<script>\n" + rd("vendor/d3.v7.9.0.min.js") + "\n</script>\n<script>\n" +
                 data_js + "\n</script>\n<script>\n" + rd("dash-shim.js") + "\n</script>",
                 "<script>window.DASH_SHIM_START();</script>")
    open(os.path.join(HERE, "psx-screener-single-file.html"), "w", encoding="utf-8").write(single)
    print(f"built standalone.html, psx-screener-single-file.html ({len(single)/1e6:.1f} MB) and data.js from {a.data} (as of {as_of})")


if __name__ == "__main__":
    main()
