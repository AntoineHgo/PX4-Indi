import json, math, os, sys
d, scen = sys.argv[1], sys.argv[2]
ok = True
def out(msg):
    print(msg)
try:
    run = json.load(open(os.path.join(d, "run.json")))
except Exception as e:
    print("FAIL run.json:", e); sys.exit(1)
print("exit_status:", run.get("exit_status"), "metrics_status:", run.get("metrics_status"))
if run.get("exit_status") != "ok": ok = False
mp = os.path.join(d, "metrics.json")
if not os.path.exists(mp):
    print("FAIL metrics.json missing"); sys.exit(1)
m = json.load(open(mp))
print("metrics top keys:", sorted(m.keys()))
nonfin = []
def walk(x, p):
    if isinstance(x, dict):
        for k, v in x.items(): walk(v, p + "." + k)
    elif isinstance(x, list):
        for i, v in enumerate(x): walk(v, p + "[%d]" % i)
    elif isinstance(x, float) and not math.isfinite(x):
        nonfin.append(p)
walk(m, "")
if nonfin: ok = False
print("non-finite leaves:", len(nonfin), nonfin[:5])
if scen == "step_roll":
    if nonfin: ok = False
    print("step block:", json.dumps(m.get("step", m.get("step_response", "MISSING")))[:600])
if scen.startswith("traj"):
    tr = m.get("trajectory")
    if not tr: ok = False; print("FAIL trajectory block missing")
    else:
        for k in ("truth", "estimate"):
            if k in tr: print("traj.%s keys:" % k, sorted(tr[k].keys())[:12])
        print("traj.time_base:", json.dumps(tr.get("time_base")))
        tb = (tr.get("time_base") or {}).get("status")
        if tb != "ok": ok = False; print("FAIL time_base.status =", tb)
print("CHECK", "PASS" if ok else "FAIL", d)
sys.exit(0 if ok else 2)
