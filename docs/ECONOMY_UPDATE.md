# Updating the economy checklist (weekly)

In Claude, the Monday run searched the web for these readings and rewrote two files. Do the same by hand, or ask ChatGPT with web browsing to return the JSON.

## 1. `workdir/config.json`

```json
{"tbill": 12.0, "policy_rate": 12.0, "zone": "Red"}
```
- `tbill` is the earnings-yield hurdle in the 33-ratio model: use the latest 12-month T-bill cut-off.
- `zone` is the course interest-rate zone: Red (rates rising), Amber or Green.

Optional keys: `capital` (default 376000) and `risk_pct` (default 1.0), used for position sizing.

## 2. `workdir/macro_src.json`

This is a list of rows: `{indicator, latest, change, direction, impact, note, source}`. The 10 rows as of 28 Oct 2026 are:
- SBP policy rate
- CPI inflation (YoY)
- 12-month T-bill yield
- Current account
- FX reserves (SBP)
- PKR / USD
- Brent crude
- Fiscal
- GDP growth outlook
- KSE-100 index

A prompt you can give ChatGPT (with browsing):

> Search for the latest SBP policy rate, Pakistan CPI inflation (YoY and core), latest 3/6/12-month T-bill cut-off yields, the current account balance, SBP FX reserves, PKR/USD, Brent crude and the KSE-100 close. Return JSON in exactly this shape (same indicator names as the file I attached): [{"indicator","latest","change","direction","impact","note","source"}]. Use "Positive"/"Negative"/"Neutral" for impact on Pakistani equities. Cite the source and date in "source".

Then run `python monitor/refresh_daily.py --skip-collect` to rebuild the dashboard with the new readings.
