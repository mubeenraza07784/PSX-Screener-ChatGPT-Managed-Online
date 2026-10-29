# Data dictionary

## data/current/stocks.json (one row per company: 489 rows, 125 columns)

| Column | Meaning |
|---|---|
| sym | Symbol (base, without XD/XR suffix) |
| psx_symbol | Symbol as listed on PSX today |
| name | Company name |
| sector | PSX sector (AHCL reclassified to Inv. Banks) |
| kse100 | KSE-100 member |
| kse30 | KSE-30 member |
| shariah | KMI/Shariah index member |
| price | Last close (PKR) |
| mcap_bn | Market cap, PKR bn |
| fiscal_year | Latest fiscal year used (YYYY-MM) |
| criteria_measured | How many of the 33 criteria could be measured |
| fund_score | Fundamental score % (33-ratio model with shrinkage) |
| tech_score | Technical score 0–100 |
| combined | 0.6×fund + 0.4×tech |
| signal | Label: Strong candidate / Strong fundamentals – wait for setup / Momentum only / Watch / Avoid / No fundamentals |
| setup | Course setup (METHOD.md §5) |
| entry | Plan entry (buy-stop, or buy-limit for FVG) |
| stop | Plan stop |
| target | Plan target (1:3) |
| reward_risk | Reward:risk of the plan |
| pe | P/E |
| pb | P/B |
| dy | Dividend yield % |
| roe | ROE % |
| de | Debt/Equity |
| sales_g | Sales growth % (latest FY) |
| np_g | Net profit growth % (latest FY) |
| op_margin | Operating margin % |
| net_margin | Net margin % |
| eps_ttm | EPS TTM |
| eps_cagr | EPS CAGR % (5y) |
| peg | PEG |
| earnings_yield | Earnings yield % (100/PE) |
| dcf_eps | DCF on EPS |
| dcf_fcf | DCF on FCF per share |
| lynch | Peter Lynch value |
| iv_fcf | Intrinsic value, FCF set (median) |
| iv_cash | Intrinsic value, cash set (median) |
| mos_fcf | Margin of safety % (FCF set) |
| mos_cash | Margin of safety % (cash set) |
| sma20 | 20-day SMA |
| sma50 | 50-day SMA |
| sma200 | 200-day SMA |
| rsi | RSI 14 |
| macd_hist_pct | MACD histogram as % of price |
| macd_cross | MACD cross in last 5 days |
| ret_1m | Return 1 month % |
| ret_3m | Return 3 months % |
| ret_6m | Return 6 months % |
| ret_1y | Return 1 year % |
| high_1y | 52-week high |
| low_1y | 52-week low |
| volatility | Annualised volatility % |
| beta | Beta vs equal-weight KSE-100 proxy |
| trend | Trend from swing pivots (Up/Down/Range; * = from moving averages) |
| support | Support |
| resistance | Resistance |
| fib_leg | Direction of the 1-year Fibonacci leg |
| fib_retrace_pct | Retracement of that leg % |
| candles | Candlestick patterns on last 3 bars |
| vol_ratio | Volume vs 50-day average |
| traded_value_m | Average traded value PKR m/day |
| alligator_daily | Alligator state, daily (bull/bear/sleep) |
| alligator_weekly | Alligator state, weekly |
| cwt_scenario | CWT scenario (S1/S2 Buy/Sell, Sleeping) |
| timeframes | Multi-timeframe reading, weekly vs daily (e.g. "W down, D sideways (S3)") |
| heikin_vs_lips | Heikin-Ashi candle vs the Lips (above/below) |
| jaw | Daily Jaw level |
| dow_structure | Dow structure (HH-HL / LH-LL) |
| rsi_divergence | RSI divergence (bull/bear) |
| fvg_bull | Nearest bullish Fair Value Gap (low-high) |
| sr_flip | Support/resistance flip: RBS = resistance became support, SBR = support became resistance, with the level |
| chart_patterns | Chart patterns found, with status |
| pattern_target | Measured target of the bullish pattern |
| entry_method | How the plan enters (buy-stop / buy-limit wording) |
| qty_for_risk | Shares for 1% risk of Rs 376,000 (capped at capital) |
| volume_leader | Among the top 40 liquid names by traded value |
| kse100_trend | KSE-100 proxy daily Alligator state (bull/bear/sleep) |
| eps_rank | S7: rank on net profit growth |
| revenue_rank | S7: rank on sales growth |
| score_rank | S7: rank on the 33-ratio score |
| aggr_avg | S7: average of the three ranks |
| aggressive_rank | S7: rank of that average (1 = best) |
| sector_median_np_g | S8: sector median net profit growth |
| liquid | Market cap ≥ PKR 2bn and ≥ PKR 5m/day traded |
| stale_financials | Latest FY older than ~16 months |
| last_price_date | Date of last price |
| cat_growth | Category score % (growth) |
| cat_valuation | Category score % (valuation) |
| cat_stability | Category score % (stability) |
| cat_free_cash_flow | Category score % (free cash flow) |
| cat_efficiency | Category score % (efficiency) |
| s_&lt;key&gt; (33 columns) | Points per criterion: 2 Good, 1 Average, 0 Bad, empty = not measurable (keys in CRITERIA.md / criteria.json) |

## data/current/strategies.json (one row per pick)

`pick_id`, `strategy` (S1–S9; SH = holdings check), `strategy_name`, `rank`, company fields as above, plus `alligator_daily`, `chart_patterns`, `qty_for_risk`, `np_g`, `sales_g`, `peg`, `sector_median_np_g` (S8), `eps_rank`, `revenue_rank`, `score_rank`, `aggressive_rank` (S7), `group`, `iv`, `mos`, `review` (holdings check), `trend`.

## Other tables

- `strategy_rules.json`: strategy, strategy_name, rule, picks
- `sectors.json`: sector, companies, avg_fund_score, avg_tech_score, median_ret_3m, red_zone
- `market.json`: one row: as_of, universe counts, KSE-100 median P/E and earnings yield, T-bill, breadth, label counts, discount rate, terminal growth
- `alerts.json`: alert_id, date, sym, name, type, detail, price, priority (newest first, max 400)
- `macro.json`: indicator, latest, change, direction, impact, note, source
- `criteria.json`: no, key, category, indicator, good, applies_to_financials

## workdir/ (state)

| File | Format |
|---|---|
| features.txt | Pipe-separated with a header row; one row per company: fundamentals (fy … dps), technicals (P … lastDate) and course fields (allD, allW, cwt, mtf, haLips, jaw, dow, swH, frL, div, fvgB, flip, pats, patN, patD, patK, patS, patE, patSL, patT, mktD, mktW). Numbers may carry B/M/K suffixes. merge.py writes it from collector output. |
| psx_meta.txt | `BASE\|PSXSYM\|SECTORCODE\|FLAGS\|PRICE\|PE\|DY\|FREEFLOAT\|VOL30`; FLAGS = KSE-100, KSE-30, KMI digits |
| names.txt | `SYM\|Company name` |
| last_signals.json | Yesterday's label, setup, levels and scores per symbol, plus `__asof__` and `__strategies__`; alerts compare against it |
| alerts_history.json | Same rows as alerts.json |
| live_watch.json | `{as_of_close, symbols:[{sym, group, close_prev, setup, entry, stop, target, jaw, alligator_daily, patterns}], intraday_syms:[~190]}` |
| live_state.json | `{date, fired:["SYM:type"]}`: live-watch alerts already raised today |
| macro_src.json, config.json | See ECONOMY_UPDATE.md |
| tech_new.txt / fund_new.txt | Collector output for merge.py (same header style as features.txt) |
