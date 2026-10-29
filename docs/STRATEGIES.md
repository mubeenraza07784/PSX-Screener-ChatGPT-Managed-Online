# Strategies (as applied by the engine)

Generated from data/current/strategy_rules.json and strategies.json (data as of 2026-10-28). Code: engine/analyze.py, section `# ---- strategies`.

Shared universe rules: *liquid* = market cap ≥ PKR 2bn and ≥ PKR 5m traded per day; *fresh financials* = latest fiscal year not older than ~16 months; a score is comparable across sectors only with 20+ of the 33 ratios measured (banks/insurers are scored on 10–11 ratios).

## S1 – Strategy 1 · Top 10% by Scoring Model

Rank liquid companies (≥PKR 2bn mcap, ≥PKR 5m/day traded, fresh financials) on the 33-ratio model; take the top 10% (14 names). Needs 20+ of the 33 ratios measured, so banks and insurers (scored on 10-11 ratios) are not ranked here. Rebalance equally each year.

**Today (14):** GHNI, PIBTL, AHCL, THCCL, NETSOL, LOADS, FCCL, DGKC, INDU, PIOC, CHCC, CSAP, ACPL, GAL

## S2 – Strategy 2 · Red-Zone sectors

Rates are rising (Red zone), so restrict the scoring model to Banks, Oil (E&P, OMC, refinery), Fertilizer, Power and Chemicals; top 10 by score. Banks are scored on fewer ratios, so at most the top 3 banks are included.

**Today (10):** NBP, UBL, BOP, SPSL, FFC, PPL, CNERGY, NRL, WAHN, FATIMA

## S3 – Strategy 3 · Lowest Price + High Beta

The 5 lowest-priced liquid stocks with beta ≥ 1 vs the KSE-100 proxy, that have a fundamental score and recent financials. Review every 3 months; swap names that leave the list. High risk – check scores before acting.

**Today (5):** WTL, BECO, KOSM, AGHA, TELE

## S4 – Strategy 4 · Score + Intrinsic Value (FCF)

Score ≥ 55% and trading below the median of DCF-FCF, DCF-EPS and Peter Lynch value; ranked by score + margin of safety (capped at 100%). Banks and insurers excluded: FCF value does not fit them.

**Today (10):** AHCL, NETSOL, GHNI, PIOC, INDU, ACPL, GAL, KTML, SPSL, PPL

## S5 – Strategy 5 · Score + Intrinsic Value (Cash)

Score ≥ 55% and trading below the median of DCF-EPS + net cash/share, DCF-EPS and Peter Lynch value; ranked by score + margin of safety (capped at 100%). Banks and insurers excluded: FCF value does not fit them.

**Today (10):** GHNI, AHCL, NETSOL, INDU, GAL, KTML, MUREB, SPSL, PPL, CNERGY

## S6 – Strategy 6 · Technical course (CWT)

From the technical course (Weeks 4–8): liquid stocks with a long setup – Alligator Scenario 1/2, a bullish reversal or continuation pattern, or a Fair-Value-Gap pullback – read on the Daily chart, the course's analysis timeframe for stocks; time the entry on your 4-hour chart. Volume leaders first, then stocks whose weekly trend also agrees. Entries are buy-stops (buy-limit at an FVG), stops below the Jaw or pattern low, targets at 1:3 reward:risk, size for 1% risk of Rs 376,000. KSE-100 (equal-weight proxy) Alligator: daily bear, weekly sleep – the course says take buy setups only when the index is bullish.

**Today (10):** AKBL, FFC, FCCL, DGKC, MCB, UBL, BOP, PIBTL, HUBC, NPL

## S7 – Strategy 7 · Aggressive rank (Sarmaaya method)

From Sir Ammar's 7 Jun 2026 session: rank each company on net profit (EPS) growth, sales growth and the 33-ratio score, average the three ranks, then rank that average (rank 1 = best). Same universe as Strategy 1 (111 liquid companies with fresh financials, banks and insurers excluded). Growth is the latest full year against the year before; top 10.

**Today (10):** STL, ACPL, GHNI, NETSOL, THCCL, IPAK, LOADS, ITANZ, GAL, POWER

## S8 – Strategy 8 · Sector growth leaders

From Sir Ammar's 12 Aug 2026 class, adapted to PSX: in sectors with 3+ rated companies, keep those whose net profit growth is above their sector's median, with sales growing, PEG of 1 or less and a score of 50%+; cheapest PEG first, top 10. PEG uses the past EPS growth rate, since forward estimates aren't available for PSX.

**Today (10):** SAZEW, GAL, NATF, SPSL, GHNI, THCCL, PIOC, IPAK, ZAL, NETSOL

## S9 – Strategy 9 · Score 70+

From the 24 May 2026 alumni session, where Sarmaaya's screener was filtered to a score above 70: every liquid company with fresh financials and 20+ of the 33 ratios measured that scores 70% or more, highest first (16 today). Banks and insurers are included only if 20+ ratios were measured.

**Today (16):** GHNI, PIBTL, AHCL, THCCL, NETSOL, LOADS, FCCL, DGKC, INDU, PIOC, CHCC, CSAP, ACPL, GAL, KTML, TGL

## SH – Your holdings check

From the 22 Feb 2026 Bear Market Strategy session: each holding and watchlist stock with its intrinsic value, margin of safety and score. A negative margin of safety or a score under 60% is flagged for review, listed first. Margin of safety uses the FCF value (cash value for banks and insurers).

**Today (13):** ABOT, COLG, DCR, HUBC, MARI, MEBL, MTL, OGDC, ENGROH, FFC, LUCK, GHNI, SAZEW
