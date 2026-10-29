import json, os
d = json.load(open("data.json"))
os.makedirs("ds", exist_ok=True)

def r(x, n=2):
    if x is None: return None
    if isinstance(x, bool): return x
    if isinstance(x, (int, float)): return round(x, n)
    return x

crit_keys = [c["key"] for c in d["criteria"]]
rows = []
for s in d["stocks"]:
    row = dict(
        sym=s["sym"], psx_symbol=s["psym"], name=s["name"], sector=s["sector"],
        kse100="Yes" if s["k100"] else "No", kse30="Yes" if s["k30"] else "No", shariah="Yes" if s["shariah"] else "No",
        price=r(s["P"]), mcap_bn=r((s.get("mcap") or 0)/1e9, 1) if s.get("mcap") else None,
        fiscal_year=s["fy"], criteria_measured=s["nCrit"],
        fund_score=r(s["fscore"], 1), tech_score=s.get("tscore"), combined=r(s.get("combined"), 1),
        signal=s["label"], setup=s.get("setup"),
        entry=r(s.get("entry")), stop=r(s.get("stop")), target=r(s.get("target")), reward_risk=r(s.get("rr")),
        pe=r(s.get("pe")), pb=r(s.get("pb")), dy=r(s.get("dy")), roe=r(s.get("roe"),1), de=r(s.get("de")),
        sales_g=r(s.get("salesG"),1), np_g=r(s.get("npG"),1), op_margin=r(s.get("opM"),1), net_margin=r(s.get("npM"),1),
        eps_ttm=r(s.get("epsT")), eps_cagr=r(s.get("epsG"),1), peg=r(s.get("peg")), earnings_yield=r(s.get("ey"),1),
        dcf_eps=r(s.get("dcfEPS"),1), dcf_fcf=r(s.get("dcfFCF"),1), lynch=r(s.get("lynch"),1),
        iv_fcf=r(s.get("ivFCF"),1), iv_cash=r(s.get("ivCash"),1), mos_fcf=r(s.get("mosFCF"),0), mos_cash=r(s.get("mosCash"),0),
        sma20=r(s.get("s20")), sma50=r(s.get("s50")), sma200=r(s.get("s200")), rsi=r(s.get("rsi"),1),
        macd_hist_pct=r(s.get("macdH"),2), macd_cross={1:"Bullish",-1:"Bearish"}.get(s.get("macdX") or 0,"None"),
        ret_1m=r(s.get("r1m"),1), ret_3m=r(s.get("r3m"),1), ret_6m=r(s.get("r6m"),1), ret_1y=r(s.get("r1y"),1),
        high_1y=r(s.get("hi")), low_1y=r(s.get("lo")), volatility=r(s.get("vol"),1), beta=r(s.get("beta"),2),
        trend=s.get("trend"), support=r(s.get("sup")), resistance=r(s.get("res")),
        fib_leg=s.get("fibLeg"), fib_retrace_pct=r((s.get("fibR") or 0)*100,1) if s.get("fibR") is not None else None,
        candles=s.get("cds") or "", vol_ratio=r(s.get("vR")), traded_value_m=r((s.get("val") or 0)/1e6,1),
        alligator_daily=s.get("allD") or "", alligator_weekly=s.get("allW") or "", cwt_scenario=s.get("cwt") or "", timeframes=s.get("mtf") or "",
        heikin_vs_lips=s.get("haLips") or "", jaw=r(s.get("jaw")), dow_structure=s.get("dow") or "", rsi_divergence=s.get("div") or "",
        fvg_bull=s.get("fvgB") or "", sr_flip=s.get("flip") or "", chart_patterns=s.get("pats") or "", pattern_target=r(s.get("proj") or s.get("patT")),
        entry_method=s.get("how") or "", qty_for_risk=s.get("qty"), volume_leader="Yes" if s.get("volLeader") else "No",
        kse100_trend=s.get("mktD") or "",
        eps_rank=s.get("epsRank"), revenue_rank=s.get("revRank"), score_rank=s.get("scoreRank"), aggr_avg=r(s.get("aggrAvg"),1),
        aggressive_rank=s.get("aggrRank"), sector_median_np_g=r(s.get("secNpG"),1),
        liquid="Yes" if s["liquid"] else "No", stale_financials="Yes" if s["stale"] else "No", last_price_date=s.get("lastDate"),
    )
    for k,c in (s.get("cat") or {}).items():
        row["cat_"+k.lower().replace(" ","_").replace("/","")] = c
    for k in crit_keys:
        row["s_"+k] = (s.get("crit") or {}).get(k)
    rows.append(row)
# make all rows share the same columns
cols = []
for rw in rows:
    for k in rw:
        if k not in cols: cols.append(k)
rows = [{k: rw.get(k) for k in cols} for rw in rows]
json.dump(rows, open("ds/stocks.json","w"), ensure_ascii=False, separators=(",",":"))

strat = []
by = {s["sym"]: s for s in d["stocks"]}
for S in d["strategies"]:
    for i, sym in enumerate(S["picks"]):
        s = by[sym]
        strat.append(dict(pick_id=f"{S['id']}-{sym}", strategy=S["id"], strategy_name=S["name"], rank=i+1, sym=sym, name=s["name"], sector=s["sector"],
            price=r(s["P"]), fund_score=r(s["fscore"],1), tech_score=s.get("tscore"), beta=r(s.get("beta"),2),
            iv_fcf=r(s.get("ivFCF"),1), mos_fcf=r(s.get("mosFCF"),0), iv_cash=r(s.get("ivCash"),1), mos_cash=r(s.get("mosCash"),0),
            setup=s.get("setup"), entry=r(s.get("entry")), stop=r(s.get("stop")), target=r(s.get("target")), reward_risk=r(s.get("rr")),
            alligator_daily=s.get("allD") or "", chart_patterns=s.get("pats") or "", qty_for_risk=s.get("qty"),
            np_g=r(s.get("npG"),1), sales_g=r(s.get("salesG"),1), peg=r(s.get("peg")), sector_median_np_g=r(s.get("secNpG"),1),
            eps_rank=s.get("epsRank"), revenue_rank=s.get("revRank"), score_rank=s.get("scoreRank"), aggressive_rank=s.get("aggrRank"),
            group=s.get("holdGroup"), iv=r(s.get("holdIv"),1), mos=r(s.get("holdMos"),0), review=s.get("review"), trend=s.get("trend")))
json.dump(strat, open("ds/strategies.json","w"), ensure_ascii=False, separators=(",",":"))
json.dump([dict(strategy=S["id"], strategy_name=S["name"], rule=S["rule"], picks=len(S["picks"])) for S in d["strategies"]], open("ds/strategy_rules.json","w"), ensure_ascii=False)

json.dump([dict(sector=x["sector"], companies=x["n"], avg_fund_score=x["fscore"], avg_tech_score=x["tscore"], median_ret_3m=x["r3m"], red_zone="Yes" if x["red"] else "No") for x in d["sectors"]],
          open("ds/sectors.json","w"), ensure_ascii=False)

u = d["universe"]; b = d["breadth"]
labels = {}
for s in d["stocks"]: labels[s["label"]] = labels.get(s["label"],0)+1
market = [dict(as_of=d["asOf"], psx_symbols=u["psxListed"], analysed=u["analysed"], with_fundamentals=u["withFundamentals"], rated_liquid=u["rated"],
               kse100_median_pe=round(d["marketPE"],2), kse100_earnings_yield=round(d["marketEY"],1), tbill=d["tbill"],
               ey_minus_tbill=round(d["marketEY"]-d["tbill"],1),
               pct_above_200dma=b["above200"], pct_uptrend=b["uptrend"], rsi_oversold=b["rsiOversold"], rsi_overbought=b["rsiOverbought"],
               strong_candidates=labels.get("Strong candidate",0), strong_wait=labels.get("Strong fundamentals – wait for setup",0),
               avoid=labels.get("Avoid",0), discount_rate=round(d["rdisc"]*100,1), terminal_growth=round(d["gterm"]*100,1))]
json.dump(market, open("ds/market.json","w"), ensure_ascii=False)

macro = json.load(open("macro_src.json"))
json.dump(macro, open("ds/macro.json","w"), ensure_ascii=False)

crit_def = []
src_rule = {"salesG":"15% or more","opG":"15% or more","npG":"15% or more","eps3v5":"3-yr avg > 5-yr avg","pe":"10 or less (10–15 average)","peg":"1 or less",
 "ey":"Greater than T-bills","pb":"1.5 or less","graham":"22.5 or less","ps":"1.5 or less (1.5–3 average)","dy":"Greater than 4%","evebitda":"10 or less",
 "opM":"12% or more (5–12% average)","npM":"8% or more (3–8% average)","taxR":"29% or more","intCov":"5 or more (2.5–5 average)","de":"0.5 or less (0.5–1 average)",
 "debt3v5":"3-yr avg < 5-yr avg","cr":"1.5 or more (0.8–1.5 average)","cfo3v5":"3-yr avg > 5-yr avg","ncfPos":"Positive","ccfo":"CCFO > CPAT","fat3v5":"3-yr avg > 5-yr avg",
 "roe":"20% or more","fcfps3v5":"3-yr avg > 5-yr avg","fcfSales":"10% or more","fcfCfo3v5":"3-yr avg > 5-yr avg","croic":"13% or more (8–13% average)",
 "invT3v5":"3-yr avg > 5-yr avg","dso3v5":"3-yr avg < 5-yr avg","dio3v5":"3-yr avg < 5-yr avg","dpo3v5":"3-yr avg > 5-yr avg","ccc3v5":"3-yr avg < 5-yr avg"}
for i,c in enumerate(d["criteria"]):
    crit_def.append(dict(no=i+1, key=c["key"], category=c["cat"], indicator=c["label"], good=src_rule[c["key"]],
                         applies_to_financials="No" if c["key"] in d["finSkip"] else "Yes"))
json.dump(crit_def, open("ds/criteria.json","w"), ensure_ascii=False)
for f in os.listdir("ds"): print(f, os.path.getsize("ds/"+f))
print(len(cols), "columns")

# alerts history (written by alerts.py)
al = json.load(open("alerts_history.json")) if os.path.exists("alerts_history.json") else []
json.dump(al, open("ds/alerts.json","w"), ensure_ascii=False, separators=(",",":"))
print("alerts", len(al))

# ---- live watch list for the 5-minute intraday task: holdings, watchlist and Strategy 6 with their course levels
HOLD = ['ABOT','COLG','DCR','ENGROH','FFC','HUBC','LUCK','MARI','MEBL','MTL','OGDC']; WATCH = ['SAZEW','GHNI']
s6 = [p["sym"] for p in strat if p["strategy"] == "S6"]
byrow = {rw["sym"]: rw for rw in rows}
lw = []
for sym in dict.fromkeys(HOLD + WATCH + s6):
    rw = byrow.get(sym)
    if not rw: continue
    lw.append(dict(sym=sym, group="holding" if sym in HOLD else "watchlist" if sym in WATCH else "strategy6",
                   close_prev=rw["price"], setup=rw["setup"], entry=rw["entry"], stop=rw["stop"], target=rw["target"], jaw=rw.get("jaw"),
                   alligator_daily=rw.get("alligator_daily"), patterns=rw.get("chart_patterns")))
K100 = [s["sym"] for s in d["stocks"] if s.get("k100")]
intraday = sorted(set([rw["sym"] for rw in rows if rw["liquid"] == "Yes"] + K100 + [x["sym"] for x in lw]))
json.dump({"as_of_close": d["asOf"], "symbols": lw, "intraday_syms": intraday}, open("live_watch.json", "w"), ensure_ascii=False)
print("live_watch", len(lw))
