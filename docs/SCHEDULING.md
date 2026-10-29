# Running it on a schedule (same times as the Claude tasks, Pakistan time)

| Job | Claude schedule | Command |
|---|---|---|
| Daily after-close refresh + alerts + report | Mon–Fri 17:43 | `python monitor/refresh_daily.py` (add `--weekly` on Mondays; `--fixed-alerts` recommended) |
| Intraday dashboard refresh | Mon–Fri 10:07, 11:07 … 15:07 | `python monitor/refresh_intraday.py` |
| Live watch (holdings / watchlist / Strategy 6 levels) | Mon–Fri 08:33 … 15:33, hourly | `python monitor/live_watch.py` |

The computer must be on and logged in. The scripts open a visible browser window by default; `--headless` hides it, but the sites may refuse headless browsers.

## Windows (Task Scheduler)

Create one task per job:
- **Trigger:** Weekly, Mon–Fri, at the time above. For the hourly jobs, set "Repeat task every 1 hour for a duration of 7 hours".
- **Action:** start a program.
  - Program: `C:\path\to\python.exe`
  - Arguments: `monitor\refresh_daily.py --fixed-alerts`
  - Start in: the folder of this export
- Tick "Run only when user is logged on", so the browser window can open.

Or from a terminal, one line per job:
```bat
schtasks /Create /TN "PSX daily" /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 17:43 /TR "cmd /c cd /d C:\psx-strategy-screener && python monitor\refresh_daily.py --fixed-alerts >> reports\daily.log 2>&1"
```

## macOS / Linux (cron, computer clock set to Asia/Karachi)

```cron
43 17 * * 1-5   cd ~/psx-strategy-screener && python3 monitor/refresh_daily.py --fixed-alerts >> reports/daily.log 2>&1
7 10-15 * * 1-5 cd ~/psx-strategy-screener && python3 monitor/refresh_intraday.py >> reports/intraday.log 2>&1
33 8-15 * * 1-5 cd ~/psx-strategy-screener && python3 monitor/live_watch.py >> reports/live.log 2>&1
```

On Mondays, run the daily job with `--weekly` instead. The economy table is updated by hand; see ECONOMY_UPDATE.md.

## Getting the alerts on your phone

Claude sent push notifications. Here, the report and the live-watch table are printed and saved under `reports/`. To receive them on your phone, add a final step that sends `reports/<date>.md` to yourself, for example by email or a Telegram bot. Keep any bot token in an environment variable on your computer, never in these files.
