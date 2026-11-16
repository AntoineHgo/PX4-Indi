import sys, numpy as np
sys.path.insert(0, "indi_flight/bench")
import a21_compare_s41 as A
from scipy.optimize import least_squares
d = {k: A.load(v) for k, v in A.FILES.items()}
f = np.concatenate([x[0] for x in d.values()]); db = np.concatenate([x[1] for x in d.values()]); ph = np.concatenate([x[2] for x in d.values()])
s = (f >= 2) & (f <= 12.7)
def run(label, names, x0, lo, hi, base):
    def r(x):
        kw = dict(base); kw.update(dict(zip(names, x)))
        e1, e2 = A.err(lambda w: A.L_ext(w, **kw), f[s], db[s], ph[s]); return A.cost_vec(e1, e2)
    q = least_squares(r, x0, bounds=(lo, hi)); kw = dict(base); kw.update(dict(zip(names, q.x)))
    e1, e2 = A.err(lambda w: A.L_ext(w, **kw), f[s], db[s], ph[s])
    m = A.MM.margins_of(lambda w, fs, **k: A.L_ext(w, fs, **k), 800.0, **kw)
    print(label, dict(zip(names, np.round(q.x, 5))), "rms %.2f" % A.rms_eq(e1, e2), "PM %.1f@%.2f GM %.1f@%.2f" % (m["pm_deg"], m["crossings"][0]["f_c"], m["gm_db"], m["phase_crossings"][0]["f"]))
P = A.PATT_AIRFRAME
run("ATT8 + g (lat=0)", ["g"], [1.3], [0.5], [3], dict(Patt=P))
run("ATT8 + g, lat=1 sample (integer)", ["g"], [1.3], [0.5], [3], dict(Patt=P, lat=1))
run("ATT8 + g, lat=2", ["g"], [1.3], [0.5], [3], dict(Patt=P, lat=2))
run("ATT8 + g + tx lag", ["g", "tx"], [1.3, 0.001], [0.5, 0], [3, 0.1], dict(Patt=P))
run("ATT8 + g + tau_r", ["g", "tau_r"], [1.3, 0.033], [0.5, 0.01], [3, 0.3], dict(Patt=P))
run("ATT free + g", ["g", "Patt"], [1.3, 8], [0.5, 0], [3, 40], {})
run("ATT free + g + Td", ["g", "Patt", "Td"], [1.3, 8, 0.001], [0.5, 0, 0], [3, 40, 0.05], {})
run("g only + Td (no ATT)", ["g", "Td"], [1.3, 0.001], [0.5, 0], [3, 0.05], {})
run("ATT8 + g + Td + Tatt", ["g", "Td", "Tatt"], [1.3, 0.001, 0.005], [0.5, 0, 0], [3, 0.05, 0.1], dict(Patt=P))
run("ATT8 + g + tau_m 0.033 (model tau as plant)", ["g", "Td"], [1.3, 0.001], [0.5, 0], [3, 0.05], dict(Patt=P, tau_m=0.033))
# 1-D scan of g and Td at ATT8 (surface)
for g in (1.0, 1.15, 1.3, 1.45):
    kw = dict(Patt=P, g=g); e1, e2 = A.err(lambda w: A.L_ext(w, **kw), f[s], db[s], ph[s]); print("scan g=%.2f rms %.2f" % (g, A.rms_eq(e1, e2)))
