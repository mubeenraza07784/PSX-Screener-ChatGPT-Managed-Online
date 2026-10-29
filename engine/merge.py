"""Merge a day's collector output into features.txt.
Usage: python3 merge.py tech_new.txt [fund_new.txt]
Each input file: first line 'sym|field|field...', then rows. Lines starting BEGIN/END are ignored.
"""
import sys
hdr = None; rows = {}
for line in open("features.txt"):
    p = line.rstrip("\n").split("|")
    if p[0] == "sym": hdr = p; continue
    if p[0]: rows[p[0]] = dict(zip(hdr, p + [""]*(len(hdr)-len(p))))
stats = {}
for fn in sys.argv[1:]:
    fhdr = None; n_upd = n_new = 0
    for line in open(fn):
        line = line.rstrip("\n")
        if not line or line.startswith("BEGIN") or line.startswith("END"): continue
        p = line.split("|")
        if p[0] == "sym":
            fhdr = p
            for k in fhdr:  # new columns (e.g. technical-course fields) are added to features.txt
                if k not in hdr:
                    hdr.append(k)
                    for r in rows.values(): r[k] = ""
            continue
        if fhdr is None: continue
        rec = dict(zip(fhdr, p))
        sym = rec["sym"]
        if sym not in rows: rows[sym] = {k: "" for k in hdr}; rows[sym]["sym"] = sym; n_new += 1
        for k, v in rec.items():
            if k in hdr and k != "sym": rows[sym][k] = v
        n_upd += 1
    stats[fn] = (n_upd, n_new)
with open("features.txt", "w") as f:
    f.write("|".join(hdr) + "\n")
    for sym, r in rows.items():
        f.write("|".join(r.get(k, "") for k in hdr) + "\n")
print("merged", stats, "total", len(rows))
