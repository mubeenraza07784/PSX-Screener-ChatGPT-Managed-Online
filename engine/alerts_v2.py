"""alerts_v2.py — OPTIONAL fixed copy of alerts.py (the original is kept unchanged next to it).

Why: alerts.py checks trade-plan events only for the old setup names
("Breakout watch (buy-stop)", "Pullback buy (limit)", "Reversal watch"). analyze.py now
names setups after the course rules ("Reversal buy-stop · Falling wedge", "CWT trend buy-stop (S1)",
"CWT pullback buy-limit (FVG)", "Continuation buy-stop · Bull flag", ...), so with alerts.py the
"Breakout triggered", "Stop hit" and "Target hit" alerts no longer fire, and "New setup" only fires
for "Reversal watch".

Change: a plan is any previous setup that had an entry and contains "buy-stop", "buy-limit",
"Breakout watch", "Pullback buy" or "Reversal watch". Buy-stop plans trigger when the close is at or above
the entry; buy-limit plans when the close is at or below the entry ("Limit filled"). Everything else
(outputs, file names, priorities, strategy membership alerts) is identical to alerts.py.

Use it with:  python3 ../engine/alerts_v2.py   (run from workdir, instead of alerts.py)
or:           python3 monitor/refresh_daily.py --fixed-alerts
"""
import json, os
d = json.load(open("data.json"))
asof = d["asOf"]
prev = json.load(open("last_signals.json")) if os.path.exists("last_signals.json") else {}
hist = json.load(open("alerts_history.json")) if os.path.exists("alerts_history.json") else []
picks = {S["id"]: S["picks"] for S in d["strategies"]}
prev_picks = prev.get("__strategies__", {})
PLAN_WORDS = ("buy-stop", "buy-limit", "Breakout watch", "Pullback buy", "Reversal watch")
is_plan = lambda s: bool(s) and any(w in s for w in PLAN_WORDS)
is_limit = lambda s: bool(s) and ("buy-limit" in s or "Pullback buy" in s)
new = []
def add(sym, name, typ, detail, price, prio):
    new.append(dict(alert_id=f"{asof}-{sym}-{typ}".replace(" ", "_"), date=asof, sym=sym, name=name, type=typ, detail=detail,
                    price=price, priority=prio))
fmt = lambda v: "" if v is None else (f"{v:,.0f}" if abs(v) >= 1000 else f"{v:,.2f}")
cur = {}
for s in d["stocks"]:
    sym, P = s["sym"], s["P"]
    cur[sym] = dict(signal=s["label"], setup=s.get("setup"), entry=s.get("entry"), stop=s.get("stop"), target=s.get("target"),
                    fscore=s.get("fscore"), tscore=s.get("tscore"), P=P)
    p = prev.get(sym)
    if not p or prev.get("__asof__") == asof: continue
    nm = s["name"]
    ps = p.get("setup")
    if is_plan(ps) and p.get("entry") and P:
        if not is_limit(ps) and P >= p["entry"]:
            add(sym, nm, "Breakout triggered", f"Closed {fmt(P)} above the buy-stop {fmt(p['entry'])} ({ps}); stop {fmt(p.get('stop'))}, target {fmt(p.get('target'))}", P, 1)
        if is_limit(ps) and P <= p["entry"]:
            add(sym, nm, "Limit filled", f"Closed {fmt(P)} at/below the buy-limit {fmt(p['entry'])} ({ps}); stop {fmt(p.get('stop'))}, target {fmt(p.get('target'))}", P, 1)
    if is_plan(ps) and p.get("stop") and P and P <= p["stop"]:
        add(sym, nm, "Stop hit", f"Closed {fmt(P)} at/below the stop {fmt(p['stop'])} from the {ps} plan", P, 1)
    if is_plan(ps) and p.get("target") and P and P >= p["target"]:
        add(sym, nm, "Target hit", f"Closed {fmt(P)} at/above the target {fmt(p['target'])}", P, 1)
    if s["label"] == "Strong candidate" and p.get("signal") != "Strong candidate":
        add(sym, nm, "New strong candidate", f"Fund {s.get('fscore')} · Tech {s.get('tscore')} (was {p.get('signal')})", P, 1)
    if p.get("signal") == "Strong candidate" and s["label"] != "Strong candidate":
        add(sym, nm, "Lost strong status", f"Now {s['label']} (Fund {s.get('fscore')} · Tech {s.get('tscore')})", P, 2)
    if is_plan(s.get("setup")) and s.get("setup") != ps and (s.get("fscore") or 0) >= 55:
        add(sym, nm, "New setup", f"{s['setup']}: entry {fmt(s.get('entry'))}, stop {fmt(s.get('stop'))}, target {fmt(s.get('target'))}, R:R {s.get('rr')}", P, 2)
    pf = p.get("fscore")
    if pf is not None and s.get("fscore") is not None and abs(s["fscore"] - pf) >= 8:
        add(sym, nm, "Score change", f"Fundamental score {pf} → {s['fscore']} (new financials)", P, 3)
if prev_picks and prev.get("__asof__") != asof:
    names = {s["sym"]: s["name"] for s in d["stocks"]}
    prices = {s["sym"]: s["P"] for s in d["stocks"]}
    for sid, lst in picks.items():
        old = set(prev_picks.get(sid, []))
        label = "Holdings check" if sid == "SH" else f"Strategy {sid[1:]}"
        for sym in lst:
            if sym not in old: add(sym, names.get(sym, sym), f"Joined {sid}", f"Now in {label} list", prices.get(sym), 2)
        for sym in old - set(lst):
            add(sym, names.get(sym, sym), f"Left {sid}", f"Dropped out of {label} list", prices.get(sym), 2)
if not prev:
    new.append(dict(alert_id=f"{asof}-baseline", date=asof, sym="—", name="Monitoring started", type="Baseline",
                    detail="First snapshot saved; alerts start from the next run.", price=None, priority=3))
existing = {a["alert_id"] for a in hist}
hist = [a for a in new if a["alert_id"] not in existing] + hist
hist = hist[:400]
json.dump(hist, open("alerts_history.json", "w"), ensure_ascii=False)
cur["__asof__"] = asof; cur["__strategies__"] = picks
json.dump(cur, open("last_signals.json", "w"))
new.sort(key=lambda a: a["priority"])
lines = [f"{a['sym']}: {a['type']} – {a['detail']}" for a in new if a["type"] != "Baseline"]
summary = f"PSX monitor {asof}: {len(lines)} alerts." + ("\n" + "\n".join(lines[:12]) if lines else " No new signals.")
open("summary.txt", "w").write(summary)
print(summary)
