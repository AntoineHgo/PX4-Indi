#!/usr/bin/env python3
"""Q19 skipped-window guard data. Usage: guard_q19.py <run dir>...  (docker, repo root). One JSON line per run.
For every vehicle_status.nav_state change c (from->to, nth of that pair) inside the airborne span (key-2 definition, h > start+0.3 m):
the 4 s windows (hop 1 s, 20-100 Hz Hann PSD, line RMS = peak +-2 Hz, key-2 detector code) overlapping [c, c+3 s], all 4 motors.
 flagged = ratio > 20 and line RMS >= 5e-4 (the chatter-line definition); report max line RMS over flagged windows (and its Hz/motor),
 and max line RMS over all overlapping windows (flagged or not) as 'any'. Windows are taken only inside the airborne span."""
import sys, os, json
sys.path.insert(0, "indi_flight/bench")
import numpy as np
import g3_checks_key2 as K
from pyulog import ULog

def one(d):
    u = ULog(os.path.join(d, "flight.ulg"), message_name_filter_list=["sim_ground_truth", "actuator_motors", "vehicle_status"])
    D = {x.name: x.data for x in u.data_list}; g = D["sim_ground_truth"]; t = g["timestamp"] * 1e-6
    pos = np.stack([g["x"], g["y"], g["z"]], 1); z0 = np.median(pos[:800, 2])
    ev = [e for e in json.load(open(os.path.join(d, "run.json")))["events"] if e["name"] == "hold"][0]
    h0, h1 = ev["t_us"] * 1e-6, ev["t_us"] * 1e-6 + ev["dur_s"]
    sgn = 1.0 if np.median(pos[(t > h0) & (t < h1), 2]) > z0 else -1.0
    h = sgn * (pos[:, 2] - z0); air = h > h[:800].mean() + 0.3; ia = np.where(air)[0]; a0, a1 = t[ia[0]], t[ia[-1]]
    mo = D["actuator_motors"]; mt = mo["timestamp"] * 1e-6; mm = (mt >= a0) & (mt <= a1)
    uu = np.stack([mo[f"control[{i}]"] for i in range(4)], 1)[mm]
    tg, gr = K.grid(mt[mm], uu)
    W = [K.psd_windows(gr[:, i], K.FS, 20, 100, rms_hz=2.0, t_off=tg[0]) for i in range(4)]
    vs = D["vehicle_status"]; ns = vs["nav_state"]; vt = vs["timestamp"] * 1e-6
    idx = np.flatnonzero(np.diff(ns) != 0) + 1; cnt = {}; out = []
    for j in idx:
        c = float(vt[j]); pair = f"{int(ns[j-1])}->{int(ns[j])}"; cnt[pair] = cnt.get(pair, 0) + 1
        best = None; anyr = 0.0; anyf = None; n = 0
        for i in range(4):
            for w in W[i]:
                ta = tg[0] + w[0]
                if ta < c + K.NAV_SKIP_S and ta + 4.0 > c:
                    n += 1
                    if w[3] > anyr: anyr, anyf = w[3], w[1]
                    if w[2] > K.RATIO and w[3] >= K.DSHOT_STEP and (best is None or w[3] > best["rms"]):
                        best = {"rms": float(w[3]), "hz": float(w[1]), "motor": i, "ratio": float(w[2]), "t_win": float(ta)}
        out.append({"pair": f"{pair}#{cnt[pair]}", "t": c, "in_span": bool(a0 <= c <= a1), "n_win": n, "flagged": best,
                    "any_rms": float(anyr), "any_hz": None if anyf is None else float(anyf)})
    return {"run": os.path.basename(d.rstrip("/")), "span": [float(a0), float(a1)], "transitions": out}

for d in sys.argv[1:]:
    print(json.dumps(one(d)), flush=True)
