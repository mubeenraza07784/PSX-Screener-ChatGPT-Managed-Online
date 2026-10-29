# Known issues found while exporting (the bot itself was left unchanged)

## 1. Trade-plan alerts no longer fire with the newer setup names (alerts.py)

`engine/alerts.py` raises the following alerts only when yesterday's setup had one of the old names "Breakout watch (buy-stop)", "Pullback buy (limit)" or "Reversal watch":
- **Breakout triggered**, **Stop hit** and **Target hit**
- **New setup**, which only fires for "Reversal watch"

`engine/analyze.py` now names setups after the technical course: "Reversal buy-stop · Falling wedge", "CWT trend buy-stop (S1)", "CWT pullback buy-limit (FVG)", "Continuation buy-stop · Bull flag", and so on. So from 29 Oct those alerts stop appearing. The six "Breakout triggered" rows in the history came from 28 Oct, before the rename.

Test, with yesterday's plans simulated as FFC buy-stop 540 (closed 549.10) and DGKC stop 200 (closed 184.60):

| Engine | Result |
|---|---|
| `alerts.py` (original) | 0 alerts |
| `alerts_v2.py` (fixed copy) | FFC "Breakout triggered", DGKC "Stop hit" |

The fixed copy also adds "Limit filled" for buy-limit plans. Use it with `python3 monitor/refresh_daily.py --fixed-alerts`. The intraday **live watch** (`monitor/live_watch.py`) is not affected; it uses the levels in `live_watch.json`.

## 2. Live dashboard missing Strategy 9 and the holdings check

At export time, the live Claude dashboard's strategy tables held Strategies 1–8 only. The stored engine produces Strategy 9 and the holdings check, and `data/current/` includes them. The next successful daily run in Claude should publish them there too.

## 3. `psx_screener_meta.py` is new code

In Claude, the weekly PSX-screener rebuild was an instruction to the assistant, not saved code. This script maps the screener's columns by header text and refuses to write fewer than 700 rows. Check the printed "columns found" line on its first run. `psx_meta.txt` changes rarely (sector, index membership), so the included file works until then.

## 4. Positions in the holdings check are hard-coded

`HOLD` and `WATCH` are written in `engine/analyze.py`, `engine/build_ds.py` and `monitor/report.py`. Change all three when your portfolio changes (`config/holdings.json` is a reference copy only).
