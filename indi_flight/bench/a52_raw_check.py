"""A-52 closing test: both G4 metric keys applied to RAW logged samples (no regridding)."""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import g4_metrics as k1
import g4_metrics_key2 as k2

UNIFORM_CRIT = 0.01  # raw samples "uniform enough" if gaps>1.5*median are <1 % of intervals and max dt < 3*median


def dt_stats(t):
    d = np.diff(t); med = np.median(d)
    return dict(n=int(t.size), median=float(med), fs=float(1 / med), dmin=float(d.min()), dmax=float(d.max()),
                maxmin=float(d.max() / d.min()), gaps=int((d > 1.5 * med).sum()), frac=float((d > 1.5 * med).mean()))


def main():
    log, t0, t1 = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
    rt, rw, ct, cu, fb, inst = k2.load(log)
    out = {"fb": fb, "inst": inst}
    raw = {}
    for nm, t, y in (("rotor", rt, rw), ("cmd", ct, cu)):
        m = (t >= t0) & (t <= t1)
        raw[nm] = (t[m], y[m])
        out["dt_" + nm] = dt_stats(t[m])
    # key1 on raw: its hf_rms on (4,n) at median rate
    r1, r2 = {}, {}
    for nm, tag in (("rotor", "R"), ("cmd", "C")):
        t, y = raw[nm]
        fs = 1 / np.median(np.diff(t))
        for fc in (20, 4):
            r1[f"{tag}{fc}"] = float(k1.hf_rms(y.T, fs, float(fc)).mean())
        # key2 on raw: swap its grid function for identity on the raw window samples (filter/RMS code untouched)
        orig = k2.uniform_grid
        k2.uniform_grid = lambda tt, yy, a, b, _fs=fs: (tt[(tt >= a) & (tt <= b)], yy[(tt >= a) & (tt <= b)], _fs)
        for fc in (20, 4):
            rms, mean, _ = k2.hp_rms(t, y, t0, t1, float(fc))
            r2[f"{tag}{fc}"] = float(rms.mean())
            if nm == "rotor":
                r2["hover_whole"] = float(mean.mean())
        k2.uniform_grid = orig
    k = int(round(k1.EDGE_S * 1 / np.median(np.diff(raw["rotor"][0]))))
    r1["hover_edge"] = float(raw["rotor"][1][k:-k].mean())
    # original (gridded) scripts for reference
    g1 = k1.metrics_from(rt, rw * 60 / (2 * np.pi), ct, cu, t0, t1)
    g2 = k2.metrics(rt, rw, ct, cu, t0, t1)
    out.update(raw_k1=r1, raw_k2=r2,
               grid_k1=dict(C20=g1["C20"]["mean"], C4=g1["C4"]["mean"], R20=g1["R20"]["mean_rad_s"], R4=g1["R4"]["mean_rad_s"], hover=g1["hover_speed_rad_s"]),
               grid_k2=dict(C20=g2["C20"], C4=g2["C4"], R20=g2["R20"], R4=g2["R4"], hover=g2["rotor_mean_rads"]))
    print(json.dumps(out, indent=1))


main()
