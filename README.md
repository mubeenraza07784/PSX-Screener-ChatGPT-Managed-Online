# PSX strategy screener – full export

> **ChatGPT-managed online private dashboard:** Follow [`docs/ONLINE_DEPLOYMENT.md`](docs/ONLINE_DEPLOYMENT.md) to connect a private GitHub repository to Streamlit Community Cloud. The `streamlit_app.py` entrypoint embeds the preserved dashboard with a prominent data-freshness notice. See [`docs/CHATGPT_MANAGER_INSTRUCTIONS.md`](docs/CHATGPT_MANAGER_INSTRUCTIONS.md) for safe ongoing ChatGPT maintenance. The cloud collector is optional and must first pass a real source-availability test.


A complete, runnable copy of the **PSX strategy screener** bot. It was exported on **29 Oct 2026** from its Claude dashboard store; the data is as of the **28 Oct 2026 close**.

The bot does four things:
1. It scores every Pakistan Stock Exchange company on the course's **33-ratio model**.
2. It values each company: DCF on EPS and FCF, a Peter Lynch value, and the margin of safety.
3. It reads each chart with the **technical course rules**: Alligator / CWT scenarios, Heikin-Ashi, Dow structure, RSI divergence, Fair Value Gaps, and chart patterns (double bottom/top, (inverse) head & shoulders, wedges, triangles, channels, flags, cup & handle), plus SMA/RSI/MACD/Fibonacci/candles.
4. It applies **Strategies 1–9 and the holdings check**, raises alerts, and shows everything on a 7-tab dashboard.

Nothing here needs Claude. It needs Python 3.9+ and, for fresh data, a Chromium browser driven by Playwright.

> Signals apply the course rules mechanically. This is a research tool, not investment advice, and it never places trades.

---

## What's inside

| Folder | What it is |
|---|---|
| `dashboard/` | `index.original.html` is the dashboard page exactly as stored in Claude (HTML/CSS/JS, d3 charts). `standalone.html` is the same page running outside Claude: open it in any browser. `psx-screener-single-file.html` is the same again as one self-contained file. `dash-shim.js` and `theme.css` replace Claude's dashboard runtime and design tokens. `build_standalone.py` rebuilds the pages after a data refresh. `vendor/` holds d3 v7.9.0. |
| `engine/` | The calculation engine, unchanged from the store: `analyze.py` (scoring, valuation, technical score, course setups, strategies, holdings check), `build_ds.py` (writes the 8 dashboard tables + `live_watch.json`), `merge.py` (merges new collector output into `features.txt`) and `alerts.py` (daily alerts). `alerts_v2.py` is an optional **fixed** copy of `alerts.py`; see `docs/KNOWN_ISSUES.md`. |
| `collector/` | `collector.js` is the price, financials and **pattern-detection** collector, unchanged from the store; it runs inside a stockanalysis.com page. `run_collector.py` runs it with Playwright (replaces Claude's browser steps). `psx_intraday.py` reads today's candles and latest trades from the PSX data portal. `psx_screener_meta.py` does the weekly rebuild of sectors and index flags. |
| `monitor/` | `refresh_daily.py` runs the after-close job and `refresh_intraday.py` the hourly job during the market. `live_watch.py` checks hourly alerts for holdings, watchlist and Strategy 6. `report.py` writes the daily Markdown report. |
| `workdir/` | The bot's **state**, exactly as stored on 29 Oct (details below). |
| `data/current/` | The 8 dashboard tables, recomputed from that state with the stored engine. They include Strategy 9 and the holdings check. |
| `data/published_snapshot/` | The 8 tables exactly as the live Claude dashboard served them at export time (see the note below). |
| `config/holdings.json` | Your holdings, watchlist and capital/risk settings, collected in one place for reference. |
| `docs/` | Method, strategies, the 33 criteria, data dictionary, ChatGPT setup, scheduling, known issues, what depends on Claude, and the original scheduled-task instructions. |
| `original_store/` | The dataset descriptions and dashboard title from the Claude store, for reference. |
| `reports/` | Daily reports land here; one example is included. |

The `workdir/` state files:
- `features.txt`: per-company features for 489 companies.
- `psx_meta.txt`: PSX sector and index flags for 752 symbols.
- `names.txt`
- `last_signals.json`
- `alerts_history.json`
- `live_watch.json`
- `live_state.json`
- `macro_src.json`
- `config.json`

> **Note on the live dashboard:** at export time, the live Claude dashboard's *Strategy picks* and *Strategy rules* tables contained only Strategies 1–8. This happened because the last publish came from an older engine run, so the page's Strategy 9 and holdings-check tables showed empty there. The stored engine computes both. `data/current/` is identical to the published snapshot for everything else (verified byte for byte for the company table, and pick for pick for S1–S8).

---

## Quick start

```bash
# 1. look at the dashboard (no install needed)
open dashboard/standalone.html          # macOS;  Windows: start dashboard\standalone.html ; Linux: xdg-open

# 2. recompute everything from the saved state (no internet, standard library only)
python3 monitor/refresh_daily.py --skip-collect

# 3. fresh data (needs Playwright + Chromium)
pip install -r requirements.txt
python -m playwright install chromium
python3 monitor/refresh_daily.py               # after 4:30 pm PKT on a trading day; ~25–35 min
python3 monitor/refresh_daily.py --weekly      # Mondays: also rebuild sector/index flags from the PSX screener
python3 monitor/refresh_intraday.py            # during market hours, hourly
python3 monitor/live_watch.py                  # during market hours, hourly
```

On Windows, use `python` instead of `python3`. To run the jobs automatically, see `docs/SCHEDULING.md` (Task Scheduler / cron, with the same times the Claude tasks used).

**Daily job steps:**
1. Run `collector.js` on stockanalysis.com. It covers every symbol's daily prices, plus one fifth of the financials, rotating by weekday.
2. `merge.py`
3. `analyze.py`
4. `alerts.py`
5. `build_ds.py`
6. Copy the tables to `data/current/` and rebuild `dashboard/standalone.html`.
7. Write `reports/<date>.md`, with the same sections as the Claude message: alerts (holdings first), holdings check, Strategy 1–9 lists, Strategy 6 setups and coverage.

**Rate limits:** if the site rate-limits (HTTP 429/403 or a "Just a moment" check), the collector stops and the rest keeps yesterday's values. It never retries around blocks or solves CAPTCHAs.

## Reproducing it in ChatGPT

See **`docs/CHATGPT_SETUP.md`**. In short, ChatGPT cannot run the browser collection on a schedule for you. Run `monitor/refresh_daily.py` on your computer, then do one of two things:
- upload `data/current/*.json` with `docs/GPT_INSTRUCTIONS.md` as the instructions, for questions and reports; or
- upload `engine/` + `workdir/` and have its code tool run the engine.

## Settings you may want to change

| Setting | Where |
|---|---|
| T-bill hurdle, policy rate, rate zone | `workdir/config.json` (`tbill`, `policy_rate`, `zone`). You can add `capital` and `risk_pct`; `analyze.py` reads them (defaults 376,000 and 1%). |
| Holdings and watchlist | `HOLD` and `WATCH` lists in `engine/analyze.py` (line 413), `engine/build_ds.py` (line 109) and `monitor/report.py`. `config/holdings.json` lists them for reference only. |
| Discount rate 17%, terminal growth 4%, DCF growth cap 15% | `engine/analyze.py` lines 8–9 and the `dcf()` function |
| Strategy thresholds (score 55/70, top 10%, PEG ≤ 1, holdings-check score 60) | `engine/analyze.py`, section `# ---- strategies` |
| Economy readings (Economy checklist tab) | `workdir/macro_src.json`; see `docs/ECONOMY_UPDATE.md` |

## What could not be exported

See **`docs/CLAUDE_RUNTIME_DEPENDENCIES.md`**. In short, these depend on Claude:
- the hosted dashboard link and its sharing
- Claude's scheduled tasks and push notifications
- the browser-tool and computer link
- the Monday web-search update of the economy table
- the AI-written messages

Each has a replacement here, except the hosted link: you host `standalone.html` yourself if you want a link. **No passwords, API keys, cookies or tokens are in this export.** None were stored in the bot. The browser profile the scripts create (`.browser-profile/`) stays on your computer and is git-ignored.

## Data sources

Prices and financials come from stockanalysis.com (S&P Global data). Sector, index membership, intraday trades and live prices come from the PSX data portal (dps.psx.com.pk). Use both for personal research and within their terms. The criteria and strategy rules come from your course material (sarmaaya.pk fundamental course, Week 12 strategies, the technical CWT course, and the recorded sessions named in `docs/STRATEGIES.md`).

`EXPORT_MANIFEST.md` lists every file with its SHA-256 and where it came from.
"# PSX-Screener-ChatGPT-Managed-Online" 
