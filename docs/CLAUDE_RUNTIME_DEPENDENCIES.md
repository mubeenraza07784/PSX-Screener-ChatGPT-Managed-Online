# What depends on Claude, and what replaces it here

| Part of the bot in Claude | Exported? | Replacement in this package |
|---|---|---|
| Dashboard page (HTML/CSS/JS, all 7 tabs, charts, filters, company checklist, position sizer) | **Yes**, verbatim (`dashboard/index.original.html`) | `dashboard/standalone.html` runs it unchanged, with `dash-shim.js` standing in for Claude's runtime |
| Claude Dashboard runtime (`dash.data`, `dash.draw`, `dash.setLink`, `dash.colors`, theme tokens, fonts, the Sources panel, freshness badges, the toolbar, sharing, comments, read-aloud, version history) | **No.** It is Claude's own code, not part of your artifact. | `dash-shim.js` implements the 4 calls the page uses. `theme.css` holds stand-in colours and system fonts. Sources and freshness panels, comments, sharing and version history are not reproduced. |
| Hosted link `claude.ai/artifact/…` (private, shareable) | **No** | Open `standalone.html` locally, or put the `dashboard/` folder on any static host (GitHub Pages, Netlify, your own site). |
| The 8 data tables (dataset files) | **Yes**. `data/published_snapshot/` holds them as served; `data/current/` holds them recomputed | Same JSON, consumed by `data.js` |
| Pipeline code and state (the store's `pipeline` collection: 14 documents) | **Yes**, verbatim: `engine/`, `collector/collector.js`, `workdir/` | none needed |
| Scheduled tasks (daily 5:43 pm, intraday hourly 10:07–15:07, live watch hourly 08:33–15:33, SAZEW/GHNI checks, portfolio P/L monitor) | **No.** They live in Claude's scheduler. Their instructions are copied to `docs/original_scheduled_task_prompts/`. | `monitor/*.py` + Task Scheduler/cron (`docs/SCHEDULING.md`) cover the first three. The portfolio P/L and SAZEW/GHNI checks were web-search jobs; ChatGPT or any assistant with web search can run them from those copied instructions. |
| Browser control of your computer (Claude's built-in browser / Claude in Chrome) | **No** | Playwright (`collector/run_collector.py`, `psx_intraday.py`, `psx_screener_meta.py`) opens a real Chromium window on your computer |
| Push notifications and chat messages from Claude | **No** | `reports/<date>.md` and console output. Hook in email/Telegram yourself if wanted (one line after `report.py`). |
| Monday web search for SBP rate, CPI, T-bills, PKR, Brent, current account, reserves | **No.** That was the assistant searching the web. | Edit `workdir/macro_src.json` and `workdir/config.json` by hand (`docs/ECONOMY_UPDATE.md`), or ask ChatGPT with web search to produce the updated JSON |
| Explanations, judgement and report wording written by Claude in chat | **No** | `monitor/report.py` builds the tables deterministically; `docs/GPT_INSTRUCTIONS.md` makes ChatGPT write in the same style |
| Your sign-in to stockanalysis.com / PSX portal | **Not stored anywhere in the bot.** Nothing to export. | Sign in yourself in the Playwright window if needed. It is kept only in `.browser-profile/` on your computer. |
| Course PDFs/videos in your Google Drive | Not copied (they're yours in Drive) | The rules taken from them are written into the code and `docs/` |

## Things the export does differently on purpose

- `standalone.html` wraps each `<script>` of the original page in its own function scope. The Claude runtime does the same, but a plain browser page does not.
- Intraday runs write to a temporary copy of `workdir/`, so the official end-of-day history is untouched, as the Claude intraday task required.
