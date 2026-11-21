"""S181: per-motor 89 Hz / 33.5 Hz line RMS and flagged windows, key1 (g3_checks.uniform) and key2 (g3_checks_key2.grid), cruise window.
Docker, repo root: python3 indi_flight/results/freeze8_pretest_s181/lines.py"""
import sys, json, numpy as np
sys.path.insert(0, "indi_flight/bench"); sys.path.insert(0, "indi_flight/results/g4_gate_s169")
import g3_checks as k1, g3_checks_key2 as k2
from scipy.signal import periodogram
R = "indi_flight/results/freeze8_pretest_s181"
def wins(x, fs, t0):
    n = int(round(4*fs)); st = int(round(1*fs)); out = []
    for s in range(0, len(x)-n+1, st):
        f, P = periodogram(x[s:s+n], fs, window="hann", detrend="constant", scaling="density"); df = f[1]-f[0]
        b = (f >= 20) & (f <= 100); k = np.flatnonzero(b)[int(np.argmax(P[b]))]; ratio = P[k]/np.median(P[b])
        rms = lambda fc: float(np.sqrt(P[(f >= fc-2) & (f <= fc+2)].sum()*df))
        out.append(dict(t=t0+s/fs, f=float(f[k]), ratio=float(ratio), rms=rms(float(f[k])), l89=rms(89.0), l335=rms(33.5)))
    return out
for sd in (2, 3):
    D = f"{R}/cruise_typ_s{sd}"
    ev = {e["name"]: e for e in json.load(open(f"{D}/run.json"))["events"]}
    tt, pos, q, w, tm, cmd, ref, src, t_land, navc = k1.load(f"{D}/flight.ulg", 0, 1)
    cm = cmd[:, :4]
    # log-time traj start from the chatter_cruise raw header (clock offset), here: first time speed event; use header text
    hdr = open(f"{R}/chatter_raw_cruise_typ_s{sd}.txt").readline()
    a, b = hdr.split("traj (log time)")[1].split(",")[0].split("(")[0].strip().split("-"); T0 = float(a); T1 = float(b) + 1.1
    m = (tm >= T0) & (tm <= T1)
    _, cg1, fs1 = k1.uniform(tm[m], cm[m], T0, T1); tg2, g2 = k2.grid(tm[m], cm[m])
    print(f"== cruise_typ_s{sd} window {T0:.1f}-{T1:.1f} s")
    for key, get in (("key1 (fixed +-2Hz, uniform grid)", lambda i: wins(cg1[i], fs1, T0)), ("key2 (k2 grid)", lambda i: wins(g2[:, i], k2.FS, tg2[0]))):
        for i in range(4):
            W = get(i); fl = [x for x in W if x["ratio"] > 20 and x["rms"] >= 5e-4]
            print(f"{key} m{i}: windows {len(W)} flagged {len(fl)}; max line RMS 89Hz {max(x['l89'] for x in W):.2e}, 33.5Hz {max(x['l335'] for x in W):.2e}; max peak-bin line RMS {max(x['rms'] for x in W):.2e} at {max(W, key=lambda x: x['rms'])['f']:.2f} Hz")
