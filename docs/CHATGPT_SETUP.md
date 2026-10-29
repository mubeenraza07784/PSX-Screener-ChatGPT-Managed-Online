# Reproducing the bot with ChatGPT

The bot has three layers:
- **collection:** a browser on your computer reads stockanalysis.com and the PSX data portal
- **calculation:** the Python engine
- **conversation:** reports, explanations and questions

ChatGPT can take over the conversation, and it can run the calculation in its code tool. Collection should stay on your computer: the PSX intraday endpoint only answers its own web page, and both sites limit automated traffic.

ChatGPT's features (Projects, custom GPTs, the code/data-analysis tool, scheduled tasks, web browsing) change often and vary by plan. Check what your plan offers; the steps below only assume you can upload files and give standing instructions.

## Option A – recommended: run locally, ask ChatGPT

1. On your computer, schedule `monitor/refresh_daily.py` (and, if you want, the intraday and live-watch scripts). See `SCHEDULING.md`.
2. In ChatGPT, create a **Project** or a **custom GPT** named "PSX strategy screener".
3. Paste `docs/GPT_INSTRUCTIONS.md` into its instructions.
4. Upload these files as its knowledge:
   - `docs/METHOD.md`, `docs/STRATEGIES.md`, `docs/CRITERIA.md`, `docs/DATA_DICTIONARY.md`
   - the course notes you want it to cite
5. Each day, upload that day's files:
   - `reports/<date>.md`
   - `data/current/strategies.json`, `data/current/alerts.json`, `data/current/market.json`
   - `data/current/stocks.json` (≈1 MB) when you want company-level questions answered
6. Then ask, for example:
   - "Give me today's report"
   - "Why is ABOT flagged in the holdings check?"
   - "Show Strategy 6 setups with position size for Rs 376,000 at 1% risk"
   - "Compare OGDC and PPL on the 33 criteria"

The answers will come from the same numbers the dashboard shows.

## Option B: let ChatGPT's code tool run the engine

The engine uses only the Python standard library, so it runs in ChatGPT's code sandbox.
1. Zip `engine/` and `workdir/` and upload the zip. If you have new collector output, include `tech_new.txt` and `fund_new.txt` from your computer.
2. Ask: "Unzip, cd workdir, then run `python ../engine/merge.py tech_new.txt fund_new.txt` (skip missing files), `python ../engine/analyze.py`, `python ../engine/alerts_v2.py`, `python ../engine/build_ds.py`, and show me the report sections from GPT_INSTRUCTIONS."
3. Download the updated `workdir/` (`features.txt`, `last_signals.json`, `alerts_history.json`, `live_watch.json`) and keep it as tomorrow's state.

Its sandbox usually has no internet access, so it cannot run `collector.js` itself.

## Option C: the dashboard

`dashboard/psx-screener-single-file.html` is one self-contained file (≈1.5 MB). Open it in your browser, or ask ChatGPT's canvas/code tool to display it if your plan supports that. After every refresh, `refresh_daily.py` rebuilds it.

## Jobs that were plain web search in Claude

The "PSX portfolio daily monitor" (P/L, collateral, news) and the "SAZEW and GHNI price check" did not use the engine; they searched the web. Their full instructions are in `docs/original_scheduled_task_prompts/4_*.md` and `5_*.md`. Paste one into a ChatGPT scheduled task, or ask for it manually; it needs web browsing turned on.

## Keep the same guard-rails

- Report signals from the course rules; never "buy/sell" advice; never place trades.
- On a rate limit or bot check, stop. Do not retry, solve CAPTCHAs or disguise automation.
- No passwords, API keys, cookies or tokens in prompts or uploads.
