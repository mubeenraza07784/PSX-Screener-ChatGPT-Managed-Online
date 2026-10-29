import json, math, statistics as st

import os
_cfg = json.load(open("config.json")) if os.path.exists("config.json") else {}
TBILL = _cfg.get("tbill", 12.0)          # % – SBP policy rate 12% after 26-Oct-2026 hike; latest 12M T-bill ~11.5–12%
CAPITAL = _cfg.get("capital", 376000)   # PKR, for position sizing (course RRMS)
RISK_PCT = _cfg.get("risk_pct", 1.0)    # % of capital risked per trade: Weekly analysis -> Daily execution = 1% (Week 7)
R_DISC = 0.17         # discount rate = T-bill + 5% equity risk premium
G_TERM = 0.04         # terminal growth (nominal PKR, conservative)

SECTORS = {"0801":"Automobile Assembler","0802":"Auto Parts","0803":"Cable & Electrical","0804":"Cement","0805":"Chemical",
 "0806":"Closed-end Fund","0807":"Commercial Banks","0808":"Engineering","0809":"Fertilizer","0810":"Food & Personal Care",
 "0811":"Glass & Ceramics","0812":"Insurance","0813":"Inv. Banks / Securities","0814":"Jute","0815":"Leasing","0816":"Leather & Tanneries",
 "0818":"Miscellaneous","0819":"Modarabas","0820":"Oil & Gas Exploration","0821":"Oil & Gas Marketing","0822":"Paper & Packaging",
 "0823":"Pharmaceuticals","0824":"Power Generation","0825":"Refinery","0826":"Sugar","0827":"Synthetic & Rayon","0828":"Technology & Comm.",
 "0829":"Textile Composite","0830":"Textile Spinning","0831":"Textile Weaving","0832":"Tobacco","0833":"Transport","0834":"Vanaspati",
 "0835":"Woollen","0836":"REIT","0837":"ETF","0838":"Property","0839":"Apparel"}
FIN = {"0807","0812","0813","0815","0819","0836","0806"}
RED_ZONE = {"0807","0820","0821","0825","0809","0824","0805"}
# PSX files some holding companies under an operating sector; reclassify them so sector strategies stay sector-pure.
SECTOR_OVERRIDE = {"AHCL": "0813"}  # Arif Habib Corp: diversified holding co, not a fertilizer producer

def num(s):
    if s is None: return None
    s = s.strip().replace(",", "")
    if s == "" : return None
    m = 1
    if s[-1] in "TBMK":
        m = {"T":1e12,"B":1e9,"M":1e6,"K":1e3}[s[-1]]; s = s[:-1]
    try: return float(s)*m
    except: return None

# ---- PSX meta
meta = {}
for line in open("psx_meta.txt"):
    p = line.rstrip("\n").split("|")
    if len(p) < 9: continue
    base, psym, sec, fl, price, pe, dy, ff, vol = p
    meta.setdefault(base, dict(psym=psym, sec=sec, k100=fl[0]=="1", k30=fl[1]=="1", shariah=fl[2]=="1",
        pPrice=num(price), pPE=num(pe), pDY=num(dy), ff=num(ff), vol30=num(vol)))
names = dict(l.rstrip("\n").split("|",1) for l in open("names.txt") if "|" in l)

# ---- features
hdr = None; rows = []
for fn in ["features.txt"]:
    for line in open(fn):
        p = line.rstrip("\n").split("|")
        if p[0] == "sym": hdr = p; continue
        if not p[0]: continue
        rows.append(p)
TXT = {"fy","trend","fibLeg","cds","lastDate","name","sym",
       "allD","allW","cwt","mtf","ha","haLips","dow","div","fvgB","fvgS","flip","pats","patN","patD","patK","patS","mktD","mktW"}
data = {}
for p in rows:
    d = {}
    for i,k in enumerate(hdr):
        v = p[i] if i < len(p) else ""
        d[k] = v if k in TXT else num(v)
    data[d["sym"]] = d

# ---- scoring rules
def band(v, good, avg=None, higher=True):
    if v is None: return None
    if higher:
        if v >= good: return 2
        if avg is not None and v >= avg: return 1
        return 0
    else:
        if v <= good: return 2
        if avg is not None and v <= avg: return 1
        return 0
def flag(v):
    if v is None: return None
    return 2 if v >= 1 else 0

CRIT = [  # key, category, label, rule-text
 ("salesG","Growth","Sales growth","≥15% good · 5–15% avg"),
 ("opG","Growth","Operating profit growth","≥15% good · 5–15% avg"),
 ("npG","Growth","Net profit growth","≥15% good · 5–15% avg"),
 ("eps3v5","Growth","EPS 3y avg > 5y avg",""),
 ("pe","Valuation","P/E","≤10 good · 10–15 avg"),
 ("peg","Valuation","PEG","≤1 good"),
 ("ey","Valuation","Earnings yield vs T-bill",f">{TBILL}% good"),
 ("pb","Valuation","P/B","≤1.5 good"),
 ("graham","Valuation","Graham P/E×P/B","≤22.5 good"),
 ("ps","Valuation","P/S","≤1.5 good · 1.5–3 avg"),
 ("dy","Valuation","Dividend yield",">4% good"),
 ("evebitda","Valuation","EV/EBITDA","≤10 good"),
 ("opM","Stability","Operating margin","≥12% good · 5–12% avg"),
 ("npM","Stability","Net margin","≥8% good · 3–8% avg"),
 ("taxR","Stability","Tax ratio (3y)","≥29% good"),
 ("intCov","Stability","Interest coverage","≥5 good · 2.5–5 avg"),
 ("de","Stability","Debt/Equity","≤0.5 good · 0.5–1 avg"),
 ("debt3v5","Stability","Total debt 3y < 5y",""),
 ("cr","Stability","Current ratio","≥1.5 good · 0.8–1.5 avg"),
 ("cfo3v5","Stability","CFO 3y > 5y",""),
 ("ncfPos","Stability","Net change in cash +",""),
 ("ccfo","Stability","Cum. CFO > Cum. PAT",""),
 ("fat3v5","Stability","Fixed-asset turnover 3y>5y",""),
 ("roe","Stability","ROE","≥20% good"),
 ("fcfps3v5","Free cash flow","FCF/share 3y > 5y",""),
 ("fcfSales","Free cash flow","FCF / Sales","≥10% good"),
 ("fcfCfo3v5","Free cash flow","FCF/CFO 3y > 5y",""),
 ("croic","Free cash flow","CROIC","≥13% good · 8–13% avg"),
 ("invT3v5","Efficiency","Inventory turnover 3y>5y",""),
 ("dso3v5","Efficiency","Days receivable 3y<5y",""),
 ("dio3v5","Efficiency","Days inventory 3y<5y",""),
 ("dpo3v5","Efficiency","Days payable 3y>5y",""),
 ("ccc3v5","Efficiency","Cash conversion cycle 3y<5y",""),
]
FIN_SKIP = {"opG","ps","evebitda","opM","intCov","de","debt3v5","cr","cfo3v5","ncfPos","ccfo","fat3v5","fcfps3v5","fcfSales","fcfCfo3v5","croic","invT3v5","dso3v5","dio3v5","dpo3v5","ccc3v5"}

def score(d, fin):
    pe = d.get("pe"); pb = d.get("pb")
    vals = dict(d)
    vals["peg"] = (pe/d["epsG"]) if (pe and pe>0 and d.get("epsG") and d["epsG"]>0) else None
    vals["ey"] = (100/pe) if (pe and pe>0) else (0 if pe is not None and pe<=0 else None)
    vals["graham"] = (pe*pb) if (pe and pe>0 and pb and pb>0) else None
    out = {}
    for k,_,_,_ in CRIT:
        if fin and k in FIN_SKIP: out[k]=None; continue
        v = vals.get(k)
        if k in ("salesG","opG","npG"): s = band(v,15,5)
        elif k=="pe": s = None if v is None else (0 if v<=0 else band(v,10,15,False))
        elif k=="peg": s = None if v is None else band(v,1,None,False)
        elif k=="ey": s = None if v is None else (2 if v>TBILL else 0)
        elif k=="pb": s = None if v is None or v<=0 else band(v,1.5,None,False)
        elif k=="graham": s = None if v is None else band(v,22.5,None,False)
        elif k=="ps": s = None if v is None or v<=0 else band(v,1.5,3,False)
        elif k=="dy": s = None if v is None else (2 if v>4 else 0)
        elif k=="evebitda": s = None if v is None else (0 if v<=0 else band(v,10,None,False))
        elif k=="opM": s = band(v,12,5)
        elif k=="npM": s = band(v,8,3)
        elif k=="taxR": s = None if v is None else (2 if v>=29 else 0)
        elif k=="intCov": s = band(v,5,2.5)
        elif k=="de": s = None if v is None else (0 if v<0 else band(v,0.5,1,False))
        elif k=="cr": s = band(v,1.5,0.8)
        elif k=="roe": s = None if v is None else (2 if v>=20 else 0)
        elif k=="fcfSales": s = None if v is None else (2 if v>=10 else 0)
        elif k=="croic": s = band(v,13,8)
        else: s = flag(v)
        out[k] = s
    got = [s for s in out.values() if s is not None]
    K = 6  # shrink toward 50% when few criteria are measurable (e.g. banks)
    pct = round(100*(sum(got)+K)/(2*len(got)+2*K),1) if got else None
    cats = {}
    for k,c,_,_ in CRIT:
        if out[k] is None: continue
        cats.setdefault(c,[]).append(out[k])
    catpct = {c: round(100*sum(v)/(2*len(v))) for c,v in cats.items()}
    return out, pct, len(got), catpct, vals

def dcf(base, g):
    if base is None or base<=0: return None
    g = max(0.0, min(g, 0.15))
    pv = 0; e = base
    for t in range(1,6):
        e *= (1+g); pv += e/(1+R_DISC)**t
    tv = e*(1+G_TERM)/(R_DISC-G_TERM)/(1+R_DISC)**5
    return pv+tv

BULL = {"Hammer","Inverted Hammer","Bullish Engulfing","Morning Star","Bullish Marubozu","Bullish Harami"}
BEAR = {"Shooting Star","Hanging Man","Bearish Engulfing","Evening Star","Bearish Marubozu","Bearish Harami"}

# ---- Technical course (Sarmaaya CWT, Weeks 4-8) setups, long-only for PSX regular market.
#  Week 4: Alligator open & parallel + Heikin-Ashi above Lips = Scenario 1 buy, stop below Jaw; Scenario 2 = close back above Jaw
#          while the mouth points down, stop below the fractal low; sleeping Alligator = no trade. Trade only with the KSE-100 trend.
#  Week 6 (stocks): Daily = analysis timeframe, 4-hour = execution (4H trigger is checked by the user on TradingView; only daily
#          data is available here). Weekly is shown for information. Buy-stop preferred, buy-limit at a Fair Value Gap.
#  Week 7: reversal patterns (double bottom, inverse H&S, falling wedge) + RSI divergence, entry on break of the last lower high.
#  Week 8: continuation patterns (bull flag, cup & handle, ascending/symmetrical triangle, channel breakouts); ride to 1:3 reward:risk.
BULL_REV = {"Double bottom","Inverse head & shoulders","Falling wedge"}
MAX_RISK = 0.15        # max (entry - stop) / entry for an actionable plan
MAX_ENTRY_GAP = 1.10   # buy-stop no more than 10% above the last close
def _rr3(entry, stop):
    return entry + 3*(entry-stop) if entry and stop and entry > stop else None
def course_setup(d, P):
    allD, allW, cwt = d.get("allD") or "", d.get("allW") or "", d.get("cwt") or ""
    jaw, swH, frL = d.get("jaw"), d.get("swH"), d.get("frL")
    div, patN, patD, patS = d.get("div") or "", d.get("patN") or "", d.get("patD") or "", d.get("patS") or ""
    patE, patSL, patT, patK = d.get("patE"), d.get("patSL"), d.get("patT"), d.get("patK") or ""
    fvg = d.get("fvgB") or ""
    setup = None; entry = stop = None; how = ""
    bstop = lambda: (swH*1.005 if swH and swH > P else P*1.005)
    # 1) bullish pattern: forming, or broke out within the last few % (entry = breakout level, buy-stop)
    if patD == "bull" and patE and patSL and div != "bear" and (patS == "forming" or (patS == "breakout" and P <= patE*1.03)):
        if patK == "reversal" or allD != "bear":
            setup = ("Reversal" if patK == "reversal" else "Continuation") + " buy-stop · " + patN
            entry, stop = max(patE, P*1.002), patSL; how = "Buy-stop above the pattern's breakout level"
    # 2) CWT Scenario 1: open, parallel Alligator, Heikin-Ashi above the Lips; not against the weekly trend
    if setup is None and cwt == "S1 Buy" and jaw:
        setup = "CWT trend buy-stop (S1)"; entry, stop = bstop(), jaw*0.99; how = "Buy-stop above the last swing high; stop below the Jaw"
    # 3) CWT Scenario 2: mouth pointing down but price closed back above the Jaw (early reversal), or bullish RSI divergence
    if setup is None and (cwt == "S2 Buy" or (div == "bull" and allD != "bull")) and frL:
        setup = "CWT early reversal buy-stop (S2)" if cwt == "S2 Buy" else "Divergence reversal buy-stop"
        entry, stop = bstop(), frL*0.99; how = "Buy-stop above the last lower high; stop below the fractal low"
    # 4) Uptrend pulling back into a bullish Fair Value Gap that sits above the Jaw: buy-limit
    if setup is None and allD == "bull" and fvg and jaw:
        lo, hi = [float(x) for x in fvg.split("-", 1)]
        if hi > jaw and hi < P:
            setup = "CWT pullback buy-limit (FVG)"; entry, stop = hi, jaw*0.99; how = "Buy-limit at the top of the Fair Value Gap; stop below the Jaw"
    extended = False
    if setup and entry and stop:
        # keep plans actionable: buy-stop within 10% of price, risk no more than 15% of entry
        # (a lagging Jaw after a spike can sit far below price); fall back to the fractal low, else wait
        if (entry-stop)/entry > MAX_RISK and frL and frL*0.99 < entry and (entry-frL*0.99)/entry <= MAX_RISK:
            stop = frL*0.99
        if entry > P*MAX_ENTRY_GAP or (entry-stop)/entry > MAX_RISK:
            setup = None; entry = stop = None; extended = True
    if setup and not (entry and stop and entry > stop*1.005):
        setup = None; entry = stop = None
    if setup is None:
        if extended: setup = "Extended – wait for pullback"
        elif cwt == "Sleeping" or allD == "sleep": setup = "Alligator sleeping – no trade"
        elif allD == "bear" or cwt.endswith("Sell"): setup = "Downtrend – avoid"
        elif allD == "bull": setup = "Uptrend – wait for candles above Lips"
        else: setup = "Neutral"
    target = _rr3(entry, stop)
    qty = int(CAPITAL*RISK_PCT/100/(entry-stop)) if entry and stop and entry > stop else None
    if qty is not None and entry: qty = min(qty, int(CAPITAL/entry))
    mkt_ok = (d.get("mktD") or "") != "bear"
    return dict(setup=setup, entry=entry, stop=stop, target=target, proj=patT if patD == "bull" else None, how=how,
                qty=qty, mkt_ok=mkt_ok)

def tech(d):
    P = d.get("P")
    if not P: return None
    s20,s50,s200 = d.get("s20"),d.get("s50"),d.get("s200")
    rsi = d.get("rsi"); tr = d.get("trend") or ""
    up = tr.startswith("Up"); down = tr.startswith("Down")
    cds = set((d.get("cds") or "").split("+")) - {""}
    bull = bool(cds & BULL); bear = bool(cds & BEAR)
    sc = 0; mx = 0
    def add(c, w=1):
        nonlocal sc, mx
        mx += w
        if c: sc += w
    if s200: add(P>s200); add(s50 is not None and s50>s200)
    if s50: add(P>s50)
    if s20: add(P>s20)
    add(up)
    if d.get("macdH") is not None: add(d["macdH"]>0)
    if rsi is not None: add(45<=rsi<=70)
    add(bull and not bear)
    if d.get("r3m") is not None: add(d["r3m"]>0)
    pen = (1 if down else 0) + (1 if (rsi or 0)>=75 else 0) + (1 if bear and not bull else 0) + (1 if d.get("macdX")==-1 else 0)
    tscore = max(0, round(100*(sc - 0.5*pen)/mx)) if mx else None
    if d.get("allD"):   # course indicators available: add them to the technical score and use the course setups
        cs = 0; cm = 0
        def cadd(c, w=1):
            nonlocal cs, cm
            cm += w
            if c: cs += w
        cadd(d.get("allD") == "bull", 2); cadd(d.get("allW") == "bull", 2); cadd(d.get("haLips") == "above")
        cadd(d.get("dow") == "HH-HL"); cadd(d.get("patD") == "bull"); cadd(d.get("div") == "bull")
        cpen = (2 if d.get("allD") == "bear" else 0) + (1 if d.get("div") == "bear" else 0) + (1 if d.get("patD") == "bear" and d.get("patS") == "breakdown" else 0)
        tscore = max(0, round(100*(sc + cs - 0.5*(pen + cpen))/(mx + cm))) if (mx + cm) else None
        r = course_setup(d, P)
        rr = round((r["target"]-r["entry"])/(r["entry"]-r["stop"]), 2) if r["entry"] and r["stop"] and r["target"] else None
        return dict(tscore=tscore, rr=rr, bull=bull, bear=bear, **r)
    sup, res, lo, hi = d.get("sup"), d.get("res"), d.get("lo"), d.get("hi")
    upTrend = bool(s200 and s50 and P>s200 and s50>s200)
    setup = "Neutral"; entry=stop=target=None
    near_sup = sup and (P-sup)/P <= 0.03
    fibR = d.get("fibR")
    if rsi is not None and rsi >= 75:
        setup = "Overbought – wait"
    elif upTrend and res and 0 <= (res-P)/P <= 0.03 and rsi is not None and 45 <= rsi <= 72:
        setup = "Breakout watch (buy-stop)"
        entry = res*1.01; stop = max(sup or entry*0.93, entry*0.92); target = entry + max(res-(sup or res*0.9), entry*0.06)
    elif upTrend and rsi is not None and 35 <= rsi <= 58 and ((d.get("fibLeg")=="up" and fibR is not None and 0.3<=fibR<=0.65) or near_sup):
        setup = "Pullback buy (limit)"
        entry = max(sup or 0, min(P, s20 or P)); stop = (sup or entry*0.95)*0.97
        target = res if res and res > entry*1.03 else hi
    elif rsi is not None and rsi <= 35 and (bull or d.get("macdX")==1 or near_sup):
        setup = "Reversal watch"
        entry = P*1.01; stop = (sup if sup and sup < P*0.995 else P*0.95)*0.97
        target = s50 if s50 and s50 > entry*1.03 else (res if res and res>entry*1.03 else entry*1.08)
    elif s200 and s50 and P<s200 and s50<s200 and down:
        setup = "Downtrend – avoid"
    elif upTrend:
        setup = "Uptrend – hold"
    rr = None
    if entry and stop and target and entry>stop: rr = round((target-entry)/(entry-stop),2)
    return dict(tscore=tscore, setup=setup, entry=entry, stop=stop, target=target, rr=rr, bull=bull, bear=bear)

import datetime as _dt
_latest = max((d.get("lastDate") or "") for d in data.values())
STALE_CUT = (_dt.date.fromisoformat(_latest) - _dt.timedelta(days=30)).isoformat()
out = []
for sym, d in data.items():
    m = meta.get(sym, {})
    sec = m.get("sec","")
    fin = sec in FIN
    finco = fin
    sec = SECTOR_OVERRIDE.get(sym, sec)  # label/strategy sector only; scoring keeps PSX code
    rec = dict(sym=sym, psym=m.get("psym",sym), name=names.get(sym, sym), sec=sec, sector=SECTORS.get(sec,"Other"), fin=finco,
               k100=m.get("k100",False), k30=m.get("k30",False), shariah=m.get("shariah",False))
    P = d.get("P") or m.get("pPrice")
    rec["P"] = P
    if m.get("pDY"): d["dy"] = m["pDY"]          # PSX official dividend yield preferred
    if d.get("pe") is None and m.get("pPE"): d["pe"] = m["pPE"] or None
    crit, pct, n, catpct, vals = score(d, fin) if d.get("fy") else ({},None,0,{},{})
    rec.update(fy=d.get("fy") or "", nCrit=n, fscore=pct if n>=10 else None, cat=catpct, crit=crit)
    for k in ["salesG","npG","pe","pb","dy","roe","de","opM","npM","epsT","epsG","mcap","croic","cr"]:
        rec[k] = d.get(k)
    rec["peg"] = vals.get("peg") if vals else None
    rec["ey"] = vals.get("ey") if vals else None
    # intrinsic values
    g = (d.get("epsG") or 0)/100
    dE = dcf(d.get("epsT"), g)
    fbase = d.get("fcfps3") if (d.get("fcfps3") or 0)>0 else d.get("fcfpsT")
    dF = None if fin else dcf(fbase, g)
    lynch = None
    if d.get("epsT") and d["epsT"]>0:
        gr = min(max(d.get("epsG") or 0,0),25) + (d.get("dy") or 0)
        lynch = d["epsT"]*min(gr,25) if gr>0 else None
    def med(xs):
        xs=[x for x in xs if x is not None and x>0]
        return st.median(xs) if xs else None
    cps = d.get("cashps") or 0
    ivF = med([dF, dE, lynch])
    ivC = med([(dE + cps) if dE else None, dE, lynch])
    rec.update(dcfEPS=dE, dcfFCF=dF, lynch=lynch, ivFCF=ivF, ivCash=ivC,
               mosFCF=(ivF/P-1)*100 if ivF and P else None, mosCash=(ivC/P-1)*100 if ivC and P else None)
    # technicals
    for k in ["s20","s50","s200","rsi","macdH","macdX","r1m","r3m","r6m","r1y","hi","lo","vol","beta","trend","sup","res","fibLeg","fibR","cds","vR","val","lastDate",
              "allD","allW","cwt","mtf","haLips","jaw","dow","div","fvgB","flip","pats","patN","patD","patS","patT","mktD","mktW"]:
        rec[k] = d.get(k)
    t = tech(d) or {}
    if (d.get("lastDate") or "") < STALE_CUT:   # no trade in the last month
        t = dict(tscore=None, setup="No recent trading", entry=None, stop=None, target=None, rr=None)
    rec.update(t)
    rec["liquid"] = bool((d.get("val") or 0) >= 5e6 and (d.get("mcap") or 0) >= 2e9)
    rec["stale"] = bool(rec["fy"] and rec["fy"] < (_dt.date.fromisoformat(_latest) - _dt.timedelta(days=490)).isoformat()[:7])
    fs, ts = rec.get("fscore"), rec.get("tscore")
    if fs is None: label = "No fundamentals"
    elif fs>=60 and (ts or 0)>=60: label = "Strong candidate"
    elif fs>=60: label = "Strong fundamentals – wait for setup"
    elif fs<45 and (ts or 0)>=60: label = "Momentum only"
    elif fs<40 and (ts or 0)<40: label = "Avoid"
    else: label = "Watch"
    rec["label"] = label
    rec["combined"] = round(0.6*fs + 0.4*(ts or 0),1) if fs is not None else None
    out.append(rec)

# ---- strategies
# Fairness rules (added 28 Oct 2026):
#  - a score is comparable only if at least MIN_CRIT of the 33 ratios were measured; banks/insurers
#    (10-11 ratios) are scored on a much smaller set, so they are kept out of the cross-sector rankings;
#  - Strategy 2 names Banks explicitly, so banks compete there among themselves for at most MAX_BANKS places;
#  - FCF/cash intrinsic values are not meaningful for financial companies, so they are left out of S4/S5;
#  - Strategy 3 needs a fundamental score and recent financials.
MIN_CRIT = 20
MAX_BANKS = 3
TIE = lambda r: (-r["fscore"], -(r.get("tscore") or 0))
rated_all = [r for r in out if r["fscore"] is not None and r["liquid"] and not r["stale"]]
rated = [r for r in rated_all if r["nCrit"] >= MIN_CRIT and not r["fin"]]
rated.sort(key=TIE)
top_n = max(1, round(len(rated)*0.10))
S1 = [r["sym"] for r in rated[:top_n]]
banks = sorted([r for r in rated_all if r["sec"] == "0807"], key=TIE)[:MAX_BANKS]
red = sorted([r for r in rated if r["sec"] in RED_ZONE] + banks, key=TIE)
S2 = [r["sym"] for r in red[:10]]
lowp = [r for r in out if r["liquid"] and r.get("beta") and r["beta"]>=1.0 and r["P"] and r["fscore"] is not None and not r["stale"]]
lowp.sort(key=lambda r: r["P"])
S3 = [r["sym"] for r in lowp[:5]]
def combo(key):
    c = [r for r in rated if r[key] is not None and r[key] > 0 and r["fscore"]>=55]
    c.sort(key=lambda r: -(r["fscore"] + min(r[key],100)*0.5))
    return [r["sym"] for r in c[:10]]
S4 = combo("mosFCF"); S5 = combo("mosCash")
# Strategy 6 · Technical course (CWT): liquid names with a course buy setup, volume leaders first (Week 4 "how to find stocks")
liq = sorted([r for r in out if r["liquid"]], key=lambda r: -(r.get("val") or 0))
VOL_LEADERS = {r["sym"] for r in liq[:40]}
for r in out: r["volLeader"] = r["sym"] in VOL_LEADERS
SETUP_RANK = lambda s: 0 if s.startswith("CWT trend") else 1 if s.startswith("Continuation") else 2 if s.startswith("Reversal") else 3 if s.startswith("CWT pullback") else 4
c6 = [r for r in out if r["liquid"] and r.get("entry") and r.get("stop") and "buy" in (r.get("setup") or "")]
c6.sort(key=lambda r: (not r["volLeader"], SETUP_RANK(r["setup"]), (r.get("allW") or "") == "bear", -(r.get("tscore") or 0), -(r.get("fscore") or 0)))
S6 = [r["sym"] for r in c6[:10]]
# Strategy 7 · Aggressive rank (added 28 Oct 2026, from Sir Ammar's 7 Jun 2026 "PSX & Sarmaaya Ranking Score" session).
#  Sarmaaya's Aggressive Rank = rank of the average of EPS rank, Revenue rank and Sarmaaya Score rank (checked against
#  ~23 rows of their table). Here: EPS rank = latest-year net profit growth, Revenue rank = latest-year sales growth,
#  Score rank = the 33-ratio score. Ranked inside the same fair universe as Strategy 1 (no banks/insurers).
for r in out: r["epsRank"] = r["revRank"] = r["scoreRank"] = r["aggrAvg"] = r["aggrRank"] = None
pool7 = [r for r in rated if r.get("npG") is not None and r.get("salesG") is not None]
def _rank(rows, key):
    for i, r in enumerate(sorted(rows, key=lambda r: -r[key])): r[key + "_rk"] = i + 1
_rank(pool7, "npG"); _rank(pool7, "salesG"); _rank(pool7, "fscore")
for r in pool7:
    r["epsRank"], r["revRank"], r["scoreRank"] = r.pop("npG_rk"), r.pop("salesG_rk"), r.pop("fscore_rk")
    r["aggrAvg"] = round((r["epsRank"] + r["revRank"] + r["scoreRank"]) / 3, 2)
for i, r in enumerate(sorted(pool7, key=lambda r: (r["aggrAvg"], r["scoreRank"]))): r["aggrRank"] = i + 1
S7 = [r["sym"] for r in sorted(pool7, key=lambda r: r["aggrRank"])[:10]]
# Strategy 8 · Sector growth leaders (from Sir Ammar's 12 Aug 2026 class, adapted to PSX): within sectors that have 3+ rated
#  companies, keep those whose net profit growth beats the sector median, with sales growing, PEG ≤ 1 and score ≥ 50; cheapest PEG first.
by_sec = {}
for r in rated:
    if r.get("npG") is not None: by_sec.setdefault(r["sec"], []).append(r["npG"])
SEC_MED = {k: st.median(v) for k, v in by_sec.items() if len(v) >= 3}
for r in out: r["secNpG"] = SEC_MED.get(r["sec"])
c8 = [r for r in rated if r["sec"] in SEC_MED and r.get("npG") is not None and r["npG"] > SEC_MED[r["sec"]]
      and (r.get("salesG") or 0) > 0 and r.get("peg") is not None and 0 < r["peg"] <= 1 and r["fscore"] >= 50]
c8.sort(key=lambda r: (r["peg"], -r["fscore"]))
S8 = [r["sym"] for r in c8[:10]]
# Strategy 9 · Score 70+ (from the 24 May 2026 alumni session: Sarmaaya screener "Cumulative Sarmaaya Score > 70").
#  Liquid companies with fresh financials and 20+ of the 33 ratios measured, score of 70% or more, highest score first.
S9_MIN = 70
c9 = sorted([r for r in rated_all if r["fscore"] >= S9_MIN and r["nCrit"] >= MIN_CRIT], key=TIE)
S9 = [r["sym"] for r in c9]
# Holdings check (from the 22 Feb 2026 "Bear Market Strategy" session): for each holding and watchlist stock, compare price with
#  intrinsic value (margin of safety) and the score; flag a negative margin of safety or a score under 60 for review.
HOLD = ['ABOT','COLG','DCR','ENGROH','FFC','HUBC','LUCK','MARI','MEBL','MTL','OGDC']; WATCH = ['SAZEW','GHNI']
HC_SCORE = 60
_by = {r["sym"]: r for r in out}
for r in out: r["holdGroup"] = r["review"] = r["holdMos"] = r["holdIv"] = None
hc = []
for sym in HOLD + WATCH:
    r = _by.get(sym)
    if not r: continue
    mos = r.get("mosCash") if r["fin"] else r.get("mosFCF")
    why = []
    if mos is None: why.append("No intrinsic value")
    elif mos < 0: why.append("Negative margin of safety")
    if r.get("fscore") is None: why.append("No score")
    elif r["fscore"] < HC_SCORE: why.append(f"Score under {HC_SCORE}")
    r["holdGroup"] = "Holding" if sym in HOLD else "Watchlist"
    r["holdMos"] = mos
    r["holdIv"] = r.get("ivCash") if r["fin"] else r.get("ivFCF")
    r["review"] = "; ".join(why) if why else "OK"
    hc.append(r)
hc.sort(key=lambda r: (r["review"] == "OK", r["holdGroup"] != "Holding", r["sym"]))
SH = [r["sym"] for r in hc]
_mk = next((r.get("mktD") for r in out if r.get("mktD")), "") or "unknown"
_mkw = next((r.get("mktW") for r in out if r.get("mktW")), "") or "unknown"
strategies = [
 dict(id="S1", name="Strategy 1 · Top 10% by Scoring Model", rule=f"Rank liquid companies (≥PKR 2bn mcap, ≥PKR 5m/day traded, fresh financials) on the 33-ratio model; take the top 10% ({top_n} names). Needs 20+ of the 33 ratios measured, so banks and insurers (scored on 10-11 ratios) are not ranked here. Rebalance equally each year.", picks=S1),
 dict(id="S2", name="Strategy 2 · Red-Zone sectors", rule="Rates are rising (Red zone), so restrict the scoring model to Banks, Oil (E&P, OMC, refinery), Fertilizer, Power and Chemicals; top 10 by score. Banks are scored on fewer ratios, so at most the top 3 banks are included.", picks=S2),
 dict(id="S3", name="Strategy 3 · Lowest Price + High Beta", rule="The 5 lowest-priced liquid stocks with beta ≥ 1 vs the KSE-100 proxy, that have a fundamental score and recent financials. Review every 3 months; swap names that leave the list. High risk – check scores before acting.", picks=S3),
 dict(id="S4", name="Strategy 4 · Score + Intrinsic Value (FCF)", rule="Score ≥ 55% and trading below the median of DCF-FCF, DCF-EPS and Peter Lynch value; ranked by score + margin of safety (capped at 100%). Banks and insurers excluded: FCF value does not fit them.", picks=S4),
 dict(id="S5", name="Strategy 5 · Score + Intrinsic Value (Cash)", rule="Score ≥ 55% and trading below the median of DCF-EPS + net cash/share, DCF-EPS and Peter Lynch value; ranked by score + margin of safety (capped at 100%). Banks and insurers excluded: FCF value does not fit them.", picks=S5),
 dict(id="S6", name="Strategy 6 · Technical course (CWT)", rule=f"From the technical course (Weeks 4–8): liquid stocks with a long setup – Alligator Scenario 1/2, a bullish reversal or continuation pattern, or a Fair-Value-Gap pullback – read on the Daily chart, the course's analysis timeframe for stocks; time the entry on your 4-hour chart. Volume leaders first, then stocks whose weekly trend also agrees. Entries are buy-stops (buy-limit at an FVG), stops below the Jaw or pattern low, targets at 1:3 reward:risk, size for {RISK_PCT:g}% risk of Rs {CAPITAL:,.0f}. KSE-100 (equal-weight proxy) Alligator: daily {_mk}, weekly {_mkw} – the course says take buy setups only when the index is bullish.", picks=S6),
 dict(id="S7", name="Strategy 7 · Aggressive rank (Sarmaaya method)", rule=f"From Sir Ammar's 7 Jun 2026 session: rank each company on net profit (EPS) growth, sales growth and the 33-ratio score, average the three ranks, then rank that average (rank 1 = best). Same universe as Strategy 1 ({len(pool7)} liquid companies with fresh financials, banks and insurers excluded). Growth is the latest full year against the year before; top 10.", picks=S7),
 dict(id="S8", name="Strategy 8 · Sector growth leaders", rule="From Sir Ammar's 12 Aug 2026 class, adapted to PSX: in sectors with 3+ rated companies, keep those whose net profit growth is above their sector's median, with sales growing, PEG of 1 or less and a score of 50%+; cheapest PEG first, top 10. PEG uses the past EPS growth rate, since forward estimates aren't available for PSX.", picks=S8),
 dict(id="S9", name="Strategy 9 · Score 70+", rule=f"From the 24 May 2026 alumni session, where Sarmaaya's screener was filtered to a score above 70: every liquid company with fresh financials and 20+ of the 33 ratios measured that scores {S9_MIN}% or more, highest first ({len(S9)} today). Banks and insurers are included only if 20+ ratios were measured.", picks=S9),
 dict(id="SH", name="Your holdings check", rule=f"From the 22 Feb 2026 Bear Market Strategy session: each holding and watchlist stock with its intrinsic value, margin of safety and score. A negative margin of safety or a score under {HC_SCORE}% is flagged for review, listed first. Margin of safety uses the FCF value (cash value for banks and insurers).", picks=SH)
]

# ---- market checklist
k100 = [r for r in out if r["k100"] and r.get("pe") and r["pe"]>0]
mpe = st.median([r["pe"] for r in k100]) if k100 else None
breadth = dict(
  above200=round(100*sum(1 for r in out if r.get("s200") and r["P"]>r["s200"])/max(1,sum(1 for r in out if r.get("s200")))),
  uptrend=round(100*sum(1 for r in out if (r.get("trend") or "").startswith("Up"))/max(1,sum(1 for r in out if r.get("trend")))),
  rsiOversold=sum(1 for r in out if r.get("rsi") is not None and r["rsi"]<30),
  rsiOverbought=sum(1 for r in out if r.get("rsi") is not None and r["rsi"]>70),
)
sector_stats = {}
for r in out:
    if r["fscore"] is None: continue
    s = sector_stats.setdefault(r["sector"], dict(n=0, f=[], t=[], r3=[]))
    s["n"]+=1; s["f"].append(r["fscore"])
    if r.get("tscore") is not None: s["t"].append(r["tscore"])
    if r.get("r3m") is not None: s["r3"].append(r["r3m"])
sectors = sorted([dict(sector=k, n=v["n"], fscore=round(st.mean(v["f"]),1), tscore=round(st.mean(v["t"]),1) if v["t"] else None,
                 r3m=round(st.median(v["r3"]),1) if v["r3"] else None, red=any(SECTORS.get(c)==k for c in RED_ZONE)) for k,v in sector_stats.items() if v["n"]>=2],
                 key=lambda x:-x["fscore"])

def clean(o):
    if isinstance(o, float):
        if math.isnan(o) or math.isinf(o): return None
        return round(o, 4) if abs(o) < 1e6 else round(o)
    if isinstance(o, dict): return {k: clean(v) for k,v in o.items()}
    if isinstance(o, list): return [clean(v) for v in o]
    return o

res = dict(asOf=max((r.get("lastDate") or "") for r in out), tbill=TBILL, rdisc=R_DISC, gterm=G_TERM, criteria=[dict(key=k,cat=c,label=l,rule=t) for k,c,l,t in CRIT],
           finSkip=sorted(FIN_SKIP), stocks=out, strategies=strategies, marketPE=mpe, marketEY=(100/mpe if mpe else None), breadth=breadth, sectors=sectors,
           universe=dict(psxListed=len(meta), analysed=len(out), withFundamentals=sum(1 for r in out if r["fscore"] is not None), rated=len(rated)))
json.dump(clean(res), open("data.json","w"), ensure_ascii=False, separators=(",",":"))
print("stocks", len(out), "rated", len(rated), "withF", res["universe"]["withFundamentals"], "top_n", top_n)
print("marketPE", mpe, "breadth", breadth)
for s in strategies: print(s["id"], s["picks"])
lab = {}
for r in out: lab[r["label"]] = lab.get(r["label"],0)+1
print(lab)
setups = {}
for r in out: setups[r.get("setup")] = setups.get(r.get("setup"),0)+1
print(setups)
