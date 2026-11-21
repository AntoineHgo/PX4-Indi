#!/usr/bin/env python3
"""S176 cruise chatter localisation. Docker, repo root:
 indi_project/docker/run.sh -n chatc -t 900 -- python3 indi_flight/results/g4_gate_s169/chatter_cruise_s176.py <run dirs>
Reuses chatter_s175.py (band_track, runs_of, detect) with the Q14 flag at both RMS widths: old +-2 bins (+-0.5 Hz) and
fixed +-2 Hz (g3_checks.CMD_RMS_HZ). Adds trajectory-phase and speed/acceleration classification of flagged windows."""
import sys, os, json
import numpy as np
sys.path.insert(0, "indi_flight/bench"); sys.path.insert(0, "indi_flight/results/g4_gate_s169")
import g3_checks as k1, g3_checks_key2 as k2
import chatter_s175 as c
from scipy.signal import periodogram
from pyulog import ULog

def track(t, u, hz, win=4.0, hop=0.5):
    tg, g, fs = k1.uniform(t, u, t[0], t[-1]); n = int(win * fs); out = []
    for s in range(0, g.shape[1] - n + 1, int(hop * fs)):
        best = (0.0, 0.0, False)
        for m in range(4):
            f, P = periodogram(g[m, s:s+n], fs, window="hann", detrend="constant", scaling="density")
            bb = (f >= 20) & (f <= 100); k = int(np.argmax(P[bb])); kk = np.flatnonzero(bb)[k]
            hb = 2 if hz is None else int(round(hz * win))
            rms = float(np.sqrt(P[max(kk-hb, 0):kk+hb+1].sum() * (f[1]-f[0])))
            if P[bb][k] > 20*np.median(P[bb]) and rms > best[0]: best = (rms, float(f[kk]), rms >= c.STEP)
        out.append((float(tg[0]) + s/fs, float(tg[0]) + s/fs + win, best[2], best[1], best[0]))
    return out

def main(dirs):
    L = []
    for d in dirs:
        n = os.path.basename(d.rstrip("/")); log = f"{d}/flight.ulg"
        rj = json.load(open(f"{d}/run.json")); ev = {e["name"]: e for e in rj["events"]}
        tr0 = ev["traj"]["t_us"]*1e-6; tr1 = tr0 + ev["traj"]["dur_s"]; hd1 = tr1 + ev["hold"]["dur_s"]
        h0 = ev["hold"]["t_us"]*1e-6
        tt, pos, q, w, tm, cmd, ref, src, t_land, navc = k1.load(log, h0, h0 + ev["hold"]["dur_s"])
        ul = ULog(log, ["vehicle_status", "vehicle_local_position"]); vs = ul.get_dataset("vehicle_status").data
        tv = (vs["timestamp"].astype(np.int64) - ul.start_timestamp)*1e-6
        ch = [(float(tv[i+1]), int(vs["nav_state"][i]), int(vs["nav_state"][i+1])) for i in np.flatnonzero(np.diff(vs["nav_state"]) != 0)]
        lp = ul.get_dataset("vehicle_local_position").data; tl = (lp["timestamp"].astype(np.int64) - ul.start_timestamp)*1e-6
        sp = np.hypot(lp["vx"], lp["vy"]); acc = np.abs(np.gradient(sp, tl)) if len(tl) > 2 else sp*0
        ok = np.isfinite(cmd).all(axis=1); cm = cmd[ok][:, :4]; tmo = tm[ok]
        L.append(f"### {n}  traj {tr0:.1f}-{tr1:.1f} (ramp 3 s), hold {h0:.1f}-{hd1:.1f}")
        L.append("nav_state: " + ", ".join(f"{a:.1f}: {b}->{e}" for a, b, e in ch))
        offb = [x for x in ch if x[2] == 14]; ld = [x for x in ch if x[2] == 18]
        t_off = offb[0][0] if offb else 0; t_ld = ld[0][0] if ld else 1e9
        # run.json event times are on the runner clock, log time = runner - off (OFFBOARD entry matched, +-0.3 s)
        off = rj["t_offboard_us"]*1e-6 - t_off; tr0 -= off; tr1 -= off; hd1 -= off
        L[-2] = f"### {n}  clock offset {off:.1f} s; traj (log time) {tr0:.1f}-{tr1:.1f} (ramp 3 s), hold {tr1:.1f}-{hd1:.1f}"
        phases = [("takeoff/loiter", 0, t_off), ("offb-pre-traj", t_off, tr0), ("traj-ramp", tr0, tr0+3), ("traj-cruise", tr0+3, tr1), ("hold", tr1, hd1), ("land-cmd", hd1, 1e9)]
        for lab, hz in (("fixed +-2 Hz", 2.0), ("old +-2 bins", None)):
            T = track(tmo, cm, hz); S = c.runs_of(T)
            L.append(f"[{lab}] flagged spans (t0-t1, peak Hz, max line RMS): " + ("; ".join(f"{a:.1f}-{b:.1f} ({f:.1f}, {r:.1e})" for a, b, f, r in S) or "none"))
            fl = [x for x in T if x[2]]
            L.append(f"[{lab}] flagged windows {len(fl)} of {len(T)}; max line RMS {max((x[4] for x in fl), default=0):.2e} ({max((x[4] for x in fl), default=0)/c.STEP:.1f}x floor); by phase (window centre): " +
                     ", ".join(f"{p}={sum(a <= (x[0]+x[1])/2 < b for x in fl)}/{sum(a <= (x[0]+x[1])/2 < b for x in T)}" for p, a, b in phases for _ in [0] if True))
            if hz == 2.0 and fl:
                # steady cruise: speed change small; flagged windows classification (window-mean accel)
                cs = []
                for x in fl:
                    m = (tl >= x[0]) & (tl <= x[1]); cs.append((float(np.mean(sp[m])), float(np.max(np.abs(np.diff(sp[m])/np.diff(tl[m]))) if m.sum() > 2 else 0), float(np.mean(acc[m]))))
                L.append("  flagged-window mean speed m/s range %.1f-%.1f, mean |dv/dt| m/s2 range %.2f-%.2f" % (min(a for a, b, e in cs), max(a for a, b, e in cs), min(e for a, b, e in cs), max(e for a, b, e in cs)))
                L.append("  all-window mean |dv/dt| inside traj-cruise: %.2f (lemniscate: speed never constant)" % float(np.mean(acc[(tl >= tr0+3) & (tl <= tr1)])))
        ta3 = None
        h = -pos[:, 2]; h = h - h[0]; a1 = np.flatnonzero(h > 1.0); a3 = np.flatnonzero(h > 0.3)
        skip = [(x[0], x[0]+3.0) for x in ch]
        res = {}
        for lab, (ta, te) in {"span h>1.0": (float(tt[a1[0]]), float(tt[a1[-1]])), "span h>0.3": (float(tt[a3[0]]), float(tt[a3[-1]]))}.items():
            for sk, skl in (("noskip", []), ("skip3s", skip)):
                m = (tmo >= ta) & (tmo <= te)
                _, cg, fs = k1.uniform(tmo[m], cm[m], ta, te)
                r1 = any(k1.line_detector(cg[i], fs, k1.CMD_BAND, k1.CMD_LINE_RMS, ta, skl, rms_hz=k1.CMD_RMS_HZ)["sustained"] for i in range(4))
                r0 = any(k1.line_detector(cg[i], fs, k1.CMD_BAND, k1.CMD_LINE_RMS, ta, skl)["sustained"] for i in range(4))
                r2 = c.detect(tmo, cm, ta, te, skl, "")[1]
                res[(lab, sk)] = (r1, r0, r2)
        L.append("sustained chatter key1 fixed/key1 old/key2: " + "; ".join(f"{a} {b}: {int(v[0])}/{int(v[1])}/{int(v[2])}" for (a, b), v in res.items()))
        L.append(""); print("\n".join(L[-9:]), flush=True)
    return L

if __name__ == "__main__":
    O = c.O
    dirs = sys.argv[1:] or [f"{O}/cruise_{p}_s{s}" for p in ("quiet", "typ", "harsh") for s in (1, 2, 3)]
    out = sys.argv[0].rsplit("/", 1)[0] + "/chatter_cruise_s176_raw.txt"
    open(out if not os.environ.get("RAW") else os.environ["RAW"], "w").write("\n".join(main(dirs)) + "\n")
