# Approved full-feature snapshot upload

The old cloud job failed because StockAnalysis.com displayed a bot verification page to GitHub's headless Chromium process. The dashboard and Python scoring engine are separate and work offline. **Do not circumvent website bot challenges or assume browser access authorizes automated collection.**

To update the cloud dashboard, obtain **permitted/licensed** PSX data, calculate the complete daily indicators and chart-pattern/CWT features required by `collector/collector.js` (`TECHF0 + COURSEF`), and put the resulting pipe-delimited data into `imports/tech_new.txt`. This is **not** a raw prices CSV: using fresh prices with old RSI/MACD/Alligator signals would be misleading.

- First line `sym|P|s20|...|lastDate|allD|...|mktW` and all expected fields from `collector/collector.js`, in any column order. Include at least 400 known symbols and at least 85% of the saved stock universe; all rows must have the current Karachi date and valid positive prices.
- Optional `imports/fund_new.txt`: the original collector-format fundamentals output (`sym|fy|...`), sourced with permission. If absent, fundamental information remains historical and **must** be treated as such.
- Copy `imports/source.example.json` to `imports/source.json`, set the actual source provider, permission basis and the data date, and set `permission_confirmed` to `true` **only if authorized**. Self-attestation is not a license verification.
- Repository should be **private** before committing provider files or personal position information. Never commit keys, broker credentials or private tokens.
- GitHub → Actions → `Refresh PSX data (approved import)` → Run workflow → **import_approved**. Default **validate_only** checks the old engine without claiming a fresh update.
- The pipeline checks input consistency, merges data, recalculates the original score/strategies, and requires same-day coverage before publishing. Errors leave the last published snapshot intact.

This patch deliberately **does not create a scheduled data feed**. Automated daily updates require connecting a source with explicit programmatic access rights, including the right to distribute/display the result as necessary. Existing screenshots and direct browser access alone do not grant that authorization.
