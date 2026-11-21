import sys, os
sys.path.insert(0, "indi_flight/bench"); sys.path.insert(0, "indi_flight/results/g4_gate_s169")
import g3_checks_key2 as K
base = "indi_flight/results/chatter_probe_s178/score"
for n in ("cruise_p1_s1", "cruise_p2_s1"):
    kw, _ = K.load_run(os.path.join(base, n)); r = K.analyse(**kw)
    ms = r["chatter"]["motors"]; mk = max(ms, key=lambda k: ms[k]["report_rms"] if ms[k]["n_flagged_windows"] else 0)
    m = ms[mk]; fl = [k for k, v in ms.items() if v["sustained"]]
    rt = r["item2_oscillation"]["rates"]; osc = ",".join(a for a in "pqr" if rt[a]["sustained"])
    print(n, "key2 peak %.1f Hz ratio %.0f rms %.2e chatter %s item2 %s" % (m['report_f_hz'], m['report_ratio'], m['report_rms'], fl or 'no', osc or 'pass'))
