# Method – how the numbers are made

All of this is code in `collector/collector.js` (browser side: prices, financial ratios, indicators, patterns) and `engine/analyze.py` (scoring, valuation, setups, labels, strategies). This page summarises it; the code is the reference.

## 1. Data per company (collector.js → features.txt)

- **Prices:** up to 500 daily OHLCV bars from stockanalysis.com (`/api/symbol/a/PSX-<SYM>/history?range=5Y`). It falls back to the history page or the close-only chart API.
- **Financials:** income statement, balance sheet, cash flow and ratios pages, parsed from the page's embedded `financialData`. Only 5 annual years plus TTM are used. One fifth of companies is refreshed each weekday (`fundSlice`).
- **Market proxy:** an equal-weighted index built from the KSE-100 members' daily returns. It supplies beta and the KSE-100 Alligator filter.
- Pacing is 700 ms between symbols and a 20 s timeout. A 429/403 or a "Just a moment" page stops further requests (`MON.blocked`).

## 2. Fundamental score (33 criteria)

See `CRITERIA.md` for each rule.
- Points: Good = 2, Average = 1, Bad = 0.
- Score = (points + 6) / (2 × measured + 12), as a %. The +6/+12 is shrinkage toward 50% when few ratios are measurable.
- Financial sectors skip 21 balance-sheet/cash-flow ratios.
- Earnings yield is compared with the T-bill (`config.json`, 12%).
- Category %: Growth, Valuation, Stability, Free cash flow, Efficiency.

## 3. Intrinsic value

- **DCF:** 5 years at the EPS CAGR, capped 0–15%; terminal growth 4%; discount rate 17% (T-bill + 5% equity risk premium). It is run on EPS (DCF-EPS) and on FCF per share (DCF-FCF; not used for banks/insurers).
- **Peter Lynch value** = EPS × min(growth + dividend yield, 25).
- **FCF set** = median(DCF-FCF, DCF-EPS, Lynch). **Cash set** = median(DCF-EPS + net cash/share, DCF-EPS, Lynch).
- **Margin of safety** = IV / price − 1.

## 4. Technical reading

The course indicators are computed in collector.js on the daily chart, with a weekly chart built from it:
- **Alligator** (Jaw/Teeth/Lips SMMA 13/8/5 shifted 8/5/3): daily and weekly state bull / bear / sleep; **CWT scenarios** S1 (open, parallel mouth, Heikin-Ashi above the Lips) and S2 (early reversal: close back above the Jaw).
- **Heikin-Ashi** vs Lips; **Dow structure** (HH-HL / LH-LL from swing points); **fractal low**; last swing high.
- **RSI divergence** (Week 7): the last two swing points within 80 bars, with an RSI extreme (<30 / >70) at the first.
- **Fair Value Gaps** (Week 6): unfilled 3-candle gaps in the last 60 bars; the nearest bullish one below price.
- **Chart patterns** (Weeks 7–8), each with status forming / breakout / breakdown plus entry, stop and measured target:
  - double bottom/top
  - head & shoulders and the inverse
  - rising/falling wedge
  - ascending/descending/symmetrical triangle
  - ascending/descending channel
  - bull/bear flag
  - cup & handle and inverted cup & handle
- **Classic indicators:** SMA 20/50/200, RSI 14 (Wilder), MACD 12/26/9 (histogram % and a 5-day cross), returns 1m/3m/6m/1y, 52-week high/low, volatility, beta, trend from swing pivots, support/resistance, 1-year Fibonacci retracement, candlestick patterns on the last 3 bars, volume ratio, and traded value.

**Technical score (0–100)** counts the following, with penalties for:
- a downtrend
- RSI ≥ 75
- bearish candles
- a MACD sell cross
- a bearish daily Alligator
- bearish divergence
- a pattern breakdown

The checks counted are:
- price above SMA200 / SMA50 / SMA20, and SMA50 above SMA200
- uptrend
- MACD histogram above 0
- RSI between 45 and 70
- bullish candles
- 3-month return above 0
- daily Alligator bull (weight 2) and weekly Alligator bull (weight 2)
- Heikin-Ashi above the Lips
- Dow structure HH-HL
- a bullish pattern
- bullish divergence

## 5. Course setup → trade plan (`course_setup` in analyze.py)

The first rule that applies wins:
1. **Bullish pattern** (forming, or broke out ≤3% ago, no bearish divergence) → "Reversal/Continuation buy-stop · <pattern>". The entry is the breakout level and the stop is the pattern low.
2. **CWT Scenario 1** → "CWT trend buy-stop (S1)": buy-stop above the last swing high, stop 1% below the Jaw.
3. **CWT Scenario 2**, or bullish RSI divergence → "CWT early reversal buy-stop (S2)" / "Divergence reversal buy-stop": stop below the fractal low.
4. **Uptrend pullback** into a bullish FVG above the Jaw → "CWT pullback buy-limit (FVG)".

Guards:
- The buy-stop must be ≤ 10% above the close and the risk ≤ 15% of the entry; otherwise the plan becomes "Extended – wait for pullback".
- With no plan, the setup is one of "Alligator sleeping – no trade", "Downtrend – avoid", "Uptrend – wait for candles above Lips" or "Neutral".

Sizing:
- **Target** is at 1:3 reward:risk.
- **Quantity** = 1% of capital (Rs 376,000) ÷ (entry − stop), capped at the capital.

## 6. Labels

| Label | Rule |
|---|---|
| Strong candidate | fund ≥ 60 and tech ≥ 60 |
| Strong fundamentals – wait for setup | fund ≥ 60, tech < 60 |
| Momentum only | fund < 45 and tech ≥ 60 |
| Avoid | fund < 40 and tech < 40 |
| Watch | everything else with a score |
| No fundamentals | no financials |

Combined = 0.6 × fund + 0.4 × tech. "No recent trading" = last price more than 30 days before the latest date. Financials are stale when the latest fiscal year is older than ~16 months.

## 7. Strategies and the holdings check

See `STRATEGIES.md`. The economy zone (Red/Amber/Green) and the course's allocation table are on the Economy checklist tab; the Red zone drives Strategy 2's sector list.

## 8. Alerts

- **Daily** (`alerts.py` / `alerts_v2.py`, compared with `last_signals.json`):
  - breakout triggered, stop hit, target hit
  - new strong candidate, lost strong status
  - new setup (score ≥ 55)
  - fundamental score change ≥ 8
  - joined / left a strategy list
- **Intraday** (`live_watch.py`): for holdings, watchlist and Strategy 6, fires on:
  - buy-stop level reached, stop hit, 1:3 target reached
  - price crossing the daily Jaw
  - moves of ±5% and ±10%
