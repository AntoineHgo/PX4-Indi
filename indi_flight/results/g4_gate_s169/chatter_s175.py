#!/usr/bin/env python3
"""S175 chatter localisation + key1/key2 window comparison. Docker, repo root:
 indi_project/docker/run.sh -n chat -t 900 -- python3 indi_flight/results/g4_gate_s169/chatter_s175.py [run dirs...]
Uses bench/g3_checks.py (key1: load, line_detector) and bench/g3_checks_key2.py (key2: psd_windows, sustained, grid)."""
import sys, json, os
import numpy as np
sys.path.insert(0, "indi_flight/bench")
import g3_checks as k1, g3_checks_key2 as k2
from scipy.signal import periodogram
O = "indi_flight/results/g4_gate_s169"
STEP = 5e-4

def band_track(t, u, win=4.0, hop=0.5):
    """Q14 flag per window (checker's 4 s Hann periodogram, 20-100 Hz band, ratio > 20, line RMS +-2 bins >= 5e-4), any motor.
    Returns [(t_start, t_end, flag, peak Hz, line RMS)] for the strongest-RMS motor among those with ratio > 20."""
    from scipy.signal import periodogram
    tg, g, fs = k1.uniform(t, u, t[0], t[-1]); n = int(win * fs); out = []
    for s in range(0, g.shape[1] - n + 1, int(hop * fs)):
        best = (0.0, 0.0, False)
        for m in range(4):
            f, P = periodogram(g[m, s:s + n], fs, window="hann", detrend="constant", scaling="density")
            bb = (f >= 20) & (f <= 100); k = int(np.argmax(P[bb])); kk = np.flatnonzero(bb)[k]
            rms = float(np.sqrt(P[max(kk - 2, 0):kk + 3].sum() * (f[1] - f[0])))
            if P[bb][k] > 20 * np.median(P[bb]) and rms > best[0]: best = (rms, float(f[kk]), rms >= STEP)
        out.append((float(tg[0]) + s / fs, float(tg[0]) + s / fs + win, best[2], best[1], best[0]))
    return out

def runs_of(tr):
    seg, cur = [], None
    for a, b, fl, f, r in tr:
        if fl:
            cur = [a, b, [f], r] if cur is None else [cur[0], b, cur[2] + [f], max(cur[3], r)]
        elif cur: seg.append(cur); cur = None
    if cur: seg.append(cur)
    return [(a, b, float(np.median(fs)), r) for a, b, fs, r in seg]

def detect(t, u, ta, te, skip, rms_mode):
    """key1 and key2 chatter on the same span [ta,te] and same skip list. rms_mode 'k1' = +-2 bins (key1), 'k2' = +-2 Hz."""
    m = (t >= ta) & (t <= te)
    _, cg, fs = k1.uniform(t[m], u[m], ta, te)
    r1 = [k1.line_detector(cg[i], fs, k1.CMD_BAND, k1.CMD_LINE_RMS, ta, skip)["sustained"] for i in range(4)]
    tg, g = k2.grid(t[m], u[m]); r2 = []
    for i in range(4):
        w = k2.psd_windows(g[:, i], k2.FS, 20, 100, rms_hz=2.0, t_off=tg[0], skip=skip)
        r2.append(k2.sustained(w, rms_min=STEP) is not None)
    return any(r1), any(r2)

def main(dirs):
    L = []
    for d in dirs:
        n = os.path.basename(d.rstrip("/")); log = f"{d}/flight.ulg"
        ev = [e for e in json.load(open(f"{d}/run.json"))["events"] if e["name"] == "hold"][0]
        h0, h1 = ev["t_us"] * 1e-6, ev["t_us"] * 1e-6 + ev["dur_s"]
        tt, pos, q, w, tm, cmd, ref, src, t_land, navc = k1.load(log, h0, h1)
        from pyulog import ULog
        vs = ULog(log, ["vehicle_status"]).get_dataset("vehicle_status").data
        tv = (vs["timestamp"].astype(np.int64) - ULog(log, ["vehicle_status"]).start_timestamp) * 1e-6
        ch = [(float(tv[i + 1]), int(vs["nav_state"][i]), int(vs["nav_state"][i + 1])) for i in np.flatnonzero(np.diff(vs["nav_state"]) != 0)]
        h = -pos[:, 2]; h = h - h[0]
        a1 = np.flatnonzero(h > 1.0); a3 = np.flatnonzero(h > 0.3)
        ok = np.isfinite(cmd).all(axis=1)
        tr = band_track(tm[ok], cmd[ok][:, :4])
        segs = runs_of(tr)
        skip = [(c[0], c[0] + 3.0) for c in ch]
        L.append(f"### {n}\nhold {h0:.1f}-{h1:.1f} s (hover hold event); airborne h>1.0 m (key1) {tt[a1[0]]:.1f}-{tt[a1[-1]]:.1f} s, h>0.3 m (key2) {tt[a3[0]]:.1f}-{tt[a3[-1]]:.1f} s")
        L.append("nav_state changes (t s: from->to): " + ", ".join(f"{c[0]:.1f}: {c[1]}->{c[2]}" for c in ch))
        L.append("Q14-flagged 4 s windows (any motor), merged union [first window start - last window end s, median peak Hz, max line RMS]: "
                 + ("; ".join(f"{a:.1f}-{b:.1f} @{f:.1f} Hz {r:.1e}" for a, b, f, r in segs) or "none"))
        ph = [(7.0, "take-off"), (0, "")]
        offb = [c for c in ch if c[2] == 14]; ld = [c for c in ch if c[2] == 18]
        t_off, t_ld = (offb[0][0] if offb else None), (ld[0][0] if ld else None)
        hold_w = [x for x in tr if t_off is not None and x[0] >= t_off + 3 and x[1] <= t_ld]
        L.append(f"steady OFFBOARD hold, windows inside [{t_off:.1f}+3, {t_ld:.1f}] s: {sum(x[2] for x in hold_w)} of {len(hold_w)} windows flagged; "
                 f"max line RMS among ratio>20 windows {max((x[4] for x in hold_w), default=0):.1e}")
        pre = [x for x in tr if x[1] <= t_off + 3 and x[2]]; post = [x for x in tr if x[0] >= t_ld - 4 and x[2]]
        L.append(f"flagged windows ending before OFFBOARD+3 s (take-off/loiter phase): {len(pre)}; windows starting after AUTO_LAND-4 s: {len(post)}")
        ta1, te1 = float(tt[a1[0]]), float(tt[a1[-1]]); ta3, te3 = float(tt[a3[0]]), float(tt[a3[-1]])
        res = {}
        for lab, (ta, te) in {"key1 span h>1.0": (ta1, te1), "key2 span h>0.3": (ta3, te3)}.items():
            for sk, skl in (("no skip", []), ("3 s skip", skl := skip)):
                res[(lab, sk)] = detect(tm[ok], cmd[ok][:, :4], ta, te, skl, "")
        L.append("chatter sustained (key1 / key2 detector): " + "; ".join(f"{a}, {b}: {int(v[0])}/{int(v[1])}" for (a, b), v in res.items()))
        L.append("")
        print("\n".join(L[-8:]), flush=True)
    return L

if __name__ == "__main__":
    dirs = sys.argv[1:] or [f"{O}/hover_{p}_s{s}" for p in ("typ", "harsh") for s in (1, 2, 3)]
    open(f"{O}/chatter_s175_raw_{'pid' if 'pid' in dirs[0] else 'indi'}.txt", "w").write("\n".join(main(dirs)) + "\n")
