import sys, json, numpy as np
sys.path.insert(0, "indi_flight/bench")
import margins_est as me
t, d, x, y = me.read_csv(sys.argv[1])
bins = me.log_bins(1.0, 60.0, 10.0, per_decade=10)
res = me.frf_periodic(d, x, y, 800.0, 10.0, bins, 1, t=t)
mg = me.margins_from_frf(res)
print("n_bins", len(res["f"]), "accepted", int(res["accepted"].sum()))
print("f", np.round(res["f"], 2).tolist())
L = res.get("L")
if L is not None:
    print("|L| dB", np.round(20*np.log10(np.abs(L)), 1).tolist()); print("arg deg", np.round(np.degrees(np.angle(L)), 1).tolist())
print(json.dumps(mg, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))[:900])
