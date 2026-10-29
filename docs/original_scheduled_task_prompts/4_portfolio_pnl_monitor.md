# PSX portfolio daily monitor

Schedule (cron): `22 * * * *`  ·  Enabled: True

This is the instruction Claude ran on that schedule, copied for reference. It refers to Claude-only tools (ArtifactData, the built-in browser, SendUserMessage); the scripts in monitor/ and collector/ do the same steps outside Claude.

---

You are monitoring a Pakistan Stock Exchange (PSX) portfolio for the user after today's market close. The user wants every answer in TABLE format, in English. You are not a licensed financial advisor: report facts, numbers and news only; never give buy/sell/hold recommendations.

HOLDINGS (quantity, average buy price in PKR, haircut %):
| Symbol | Qty | Avg buy | Haircut |
| ABOT | 41 | 928.68 | 22.5 |
| COLG | 34 | 1,109.98 | 15 |
| DCR | 961 | 41.00 | 15 |
| ENGROH | 154 | 235.75 | 15 |
| FFC | 71 | 451.76 | 17.5 |
| HUBC | 147 | 188.89 | 15 |
| LUCK | 49 | 384.32 | 15 |
| MARI | 50 | 625.50 | 15 |
| MEBL | 66 | 484.75 | 15 |
| MTL | 136 | 278.89 | 15 |
| OGDC | 63 | 249.51 | 15 |
Total cost basis about Rs 347,112. Baseline on Oct 27, 2026: market value Rs 363,740, unrealized P/L +Rs 16,628, settled P/L -Rs 8,306.
WATCHLIST: SAZEW (user planned to buy it on Oct 28, 2026; quantity and price unknown, so track it as a watchlist stock only).

STEPS
1. Use WebSearch (standard mode; send searches in parallel) to find today's closing price for each holding and SAZEW, today's KSE-100 close and change, and the current Brent crude price. Good sources: dps.psx.com.pk, scstrade.com, mettisglobal.news, brecorder.com, propakistani.pk, arynews.tv. If you cannot find a reliable price for today, mark it "n/a" rather than guessing.
2. Search for news from the last 1–2 days on each symbol: financial results, dividends (declaration, ex-date, book closure), board meetings, buybacks, monthly sales data, regulatory news.
3. Compute with code (Bash/python), not mentally: each stock's market value, unrealized P/L in Rs and %, day change %, % cushion above or below cost; portfolio total value, total unrealized P/L, collateral value after haircuts; how far the KSE-100 can fall (%) before total unrealized P/L hits zero.

ALERTS (flag clearly at the top):
- Any holding that moved 3% or more today, up or down.
- Any holding that crossed its average buy price (went from profit to loss or loss to profit) or is now within 1% of it.
- Total unrealized P/L turning negative.
- KSE-100 down 2% or more on the day.
- Any results announcement, dividend declaration, ex-dividend date in the next 5 days, or major company news.

OUTPUT: send the report to the user with SendUserMessage, entirely as markdown tables:
Table 1 Alerts (or one row saying "No alerts today").
Table 2 Market: KSE-100 close and change, Brent price.
Table 3 Holdings: Symbol | Close | Day % | Value | Unrealized P/L | P/L % | Cushion to cost.
Table 4 Portfolio totals: value, unrealized P/L, collateral after haircuts, change vs Oct 27 baseline.
Table 5 News and upcoming events by symbol (only symbols with news).
Table 6 SAZEW watch: close, day %, any news.
End with a short Sources list of the pages used, and a one-line reminder that prices come from public web sources and may differ slightly from the broker terminal; if the user bought or sold anything, they should send an updated screenshot so the holdings can be updated.
