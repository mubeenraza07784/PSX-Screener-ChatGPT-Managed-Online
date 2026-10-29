"""Compare today's data.json with last_signals.json, append alerts to alerts_history.json,
write a new last_signals.json and summary.txt (for the notification)."""
import json, os
d = json.load(open("data.json"))
asof = d["asOf"]
prev = json.load(open("last_signals.json")) if os.path.exists("last_signals.json") else {}
hist = json.load(open("alerts_history.json")) if os.path.exists("alerts_history.json") else []
picks = {S["id"]: S["picks"] for S in d["strategies"]}
prev_picks = prev.get("__strategies__", {})
SETUPS = {"Breakout watch (buy-stop)", "Pullback buy (limit)", "Reversal watch"}
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
    # trade-plan events from yesterday's plan
    if p.get("setup") == "Breakout watch (buy-stop)" and p.get("entry") and P and P >= p["entry"]:
        add(sym, nm, "Breakout triggered", f"Closed {fmt(P)} above the buy-stop {fmt(p['entry'])}; stop {fmt(p.get('stop'))}, target {fmt(p.get('target'))}", P, 1)
    if p.get("setup") in SETUPS and p.get("stop") and P and P <= p["stop"]:
        add(sym, nm, "Stop hit", f"Closed {fmt(P)} at/below the stop {fmt(p['stop'])} from the {p['setup']} plan", P, 1)
    if p.get("setup") in SETUPS and p.get("target") and P and P >= p["target"]:
        add(sym, nm, "Target hit", f"Closed {fmt(P)} at/above the target {fmt(p['target'])}", P, 1)
    # signal changes
    if s["label"] == "Strong candidate" and p.get("signal") != "Strong candidate":
        add(sym, nm, "New strong candidate", f"Fund {s.get('fscore')} · Tech {s.get('tscore')} (was {p.get('signal')})", P, 1)
    if p.get("signal") == "Strong candidate" and s["label"] != "Strong candidate":
        add(sym, nm, "Lost strong status", f"Now {s['label']} (Fund {s.get('fscore')} · Tech {s.get('tscore')})", P, 2)
    if s.get("setup") in SETUPS and s.get("setup") != p.get("setup") and (s.get("fscore") or 0) >= 55:
        add(sym, nm, "New setup", f"{s['setup']}: entry {fmt(s.get('entry'))}, stop {fmt(s.get('stop'))}, target {fmt(s.get('target'))}, R:R {s.get('rr')}", P, 2)
    pf = p.get("fscore")
    if pf is not None and s.get("fscore") is not None and abs(s["fscore"] - pf) >= 8:
        add(sym, nm, "Score change", f"Fundamental score {pf} → {s['fscore']} (new financials)", P, 3)
# strategy membership changes
if prev_picks and prev.get("__asof__") != asof:
    names = {s["sym"]: s["name"] for s in d["stocks"]}
    prices = {s["sym"]: s["P"] for s in d["stocks"]}
    for sid, lst in picks.items():
        old = set(prev_picks.get(sid, []))
        for sym in lst:
            if sym not in old: add(sym, names.get(sym, sym), f"Joined {sid}", f"Now in Strategy {sid[1]} list", prices.get(sym), 2)
        for sym in old - set(lst):
            add(sym, names.get(sym, sym), f"Left {sid}", f"Dropped out of Strategy {sid[1]} list", prices.get(sym), 2)
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
