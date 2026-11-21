#!/usr/bin/env python3
"""G4 command-chatter scoring, key 1, with the Q18 A touchdown skip (GATES.md "Owner amendments S180").
Key 1 detector = bench/g3_checks.line_detector (20-100 Hz, 4 s Hann windows hop 1 s, peak > 20 x median, line RMS
peak +-2 Hz >= 5e-4, sustained = >= 3 consecutive windows). New: every 4 s window that overlaps
[ground_contact - 1 s, landed + 1 s] is skipped (counts as unflagged, breaks a run).
ground_contact = last 0->1 edge of vehicle_land_detected.ground_contact (= first rise of the final descent, after the
last airborne period); landed = first 0->1 edge of .landed at or after it. No such rise (flight ends airborne) -> nothing skipped.
Run (docker, repo root):
  indi_project/docker/run.sh -n k1s -t 900 -- python3 indi_flight/bench/g4_chatter_skip_key1.py [--extend] <out.md> <run dir>...
--extend: detector span runs to the last actuator_motors sample (descent and ground phase included); default = airborne span h > 1 m (as the gate, ends before touchdown)
Env G4_SKIP_DISABLE=1 turns the skip off (used only to break-check the self-test)."""
import os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import g3_checks as k1  # noqa: E402

PRE_S, POST_S = 1.0, 1.0


def skip_interval(gc, landed):
    """Q18 A skip interval or None."""
    if os.environ.get("G4_SKIP_DISABLE") or gc is None or landed is None:
        return None
    return (gc - PRE_S, landed + POST_S)


def landing_times(log):
    """(ground_contact, landed) log times [s] of the final touchdown, (None, None) if the flight has no landing."""
    from pyulog import ULog
    u = ULog(log, ["vehicle_land_detected"])
    x = u.get_dataset("vehicle_land_detected").data
    t = (x["timestamp"].astype(np.int64) - u.start_timestamp) * 1e-6
    return edges_to_landing(t, x["ground_contact"].astype(int), x["landed"].astype(int))


def edges_to_landing(t, gc, ld):
    rise = np.flatnonzero((gc[1:] == 1) & (gc[:-1] == 0)) + 1
    if rise.size == 0:
        return None, None
    tgc = float(t[rise[-1]])
    lr = np.flatnonzero((ld[1:] == 1) & (ld[:-1] == 0) & (t[1:] >= tgc)) + 1
    if lr.size == 0:
        return tgc, None
    return tgc, float(t[lr[0]])


def scan(tm, cmd, ta, te, skip):
    """Per 4 s window, per motor. Returns (verdict dict, rows). rows: (w0, w1, skipped, motor, peak Hz, ratio, line RMS, flagged).
    Verdict = k1.line_detector(skip=...) for the 4 motors (authoritative, same code as the gate)."""
    from scipy.signal import periodogram
    ok = np.isfinite(cmd[:, :4]).all(axis=1) & (tm >= ta) & (tm <= te)
    _, cg, fs = k1.uniform(tm[ok], cmd[ok][:, :4], ta, te)
    skl = [skip] if skip else []
    det = [k1.line_detector(cg[i], fs, k1.CMD_BAND, k1.CMD_LINE_RMS, ta, skl, rms_hz=k1.CMD_RMS_HZ) for i in range(4)]
    n, step = int(round(k1.WIN_S * fs)), int(round(k1.STEP_S * fs))
    hb = int(round(k1.CMD_RMS_HZ * k1.WIN_S)); rows = []
    for s in range(0, cg.shape[1] - n + 1, step):
        w0, w1 = ta + s / fs, ta + (s + n) / fs
        sk = bool(skl and any(w0 < tb and w1 > a for a, tb in skl))
        for m in range(4):
            f, P = periodogram(cg[m, s:s + n], fs, window="hann", detrend="constant", scaling="density")
            b = (f >= k1.CMD_BAND[0]) & (f <= k1.CMD_BAND[1]); k = int(np.argmax(P[b])); kk = np.flatnonzero(b)[k]
            ratio = float(P[b][k] / np.median(P[b]))
            rms = float(np.sqrt(P[max(kk - hb, 0):kk + hb + 1].sum() * (f[1] - f[0])))
            rows.append((w0, w1, sk, m, float(f[kk]), ratio, rms, ratio > k1.PEAK_RATIO and rms >= k1.CMD_LINE_RMS))
    return {"chatter": any(d["sustained"] for d in det), "lines": [d["lines"] for d in det],
            "skipped_windows": det[0]["skipped_windows"], "windows": det[0]["windows"]}, rows


def worst(rows, skipped):
    """Largest line RMS among ratio > 20 windows (skipped or not as asked); None if none."""
    c = [r for r in rows if r[2] == skipped and r[5] > k1.PEAK_RATIO]
    return max(c, key=lambda r: r[6]) if c else None


def score_run(d, extend=False):
    tt, pos, q, w, tm, cmd, ref, src, t_land, nav = k1.load(f"{d}/flight.ulg", 0, 0)
    h = -pos[:, 2]; h = h - h[0]
    up = np.flatnonzero(np.isfinite(h) & (h > k1.AIRBORNE_M)); ta, te = float(tt[up[0]]), float(tt[up[-1]])
    if extend:  # whole descent and ground phase: up to the last actuator_motors sample (the touchdown is inside)
        te = float(tm[-1])
    gc, ld = landing_times(f"{d}/flight.ulg"); sk = skip_interval(gc, ld)
    v, rows = scan(tm, cmd, ta, te, sk)
    v0, _ = scan(tm, cmd, ta, te, None)
    return {"ta": ta, "te": te, "gc": gc, "landed": ld, "skip": sk, "chatter": v["chatter"], "chatter_noskip": v0["chatter"],
            "n_skipped": v["skipped_windows"], "n_win": v["windows"], "worst_kept": worst(rows, False), "worst_skip": worst(rows, True),
            "flagged_kept": [r for r in rows if r[7] and not r[2]], "flagged_skip": [r for r in rows if r[7] and r[2]]}


def fmt(r):
    return "none" if r is None else f"{r[4]:.1f} Hz, x{r[5]:.0f}, {r[6]:.2e}, win {r[0]:.1f}-{r[1]:.1f} (m{r[3]})"


def spans(fl):
    """Merge flagged windows (any motor) into spans: 'start-end (Hz range, max RMS)'."""
    if not fl:
        return ""
    fl = sorted(fl, key=lambda x: x[0]); out = []; cur = [fl[0][0], fl[0][1], [fl[0][4]], fl[0][6]]
    for x in fl[1:]:
        if x[0] <= cur[1]:
            cur[1] = max(cur[1], x[1]); cur[2].append(x[4]); cur[3] = max(cur[3], x[6])
        else:
            out.append(cur); cur = [x[0], x[1], [x[4]], x[6]]
    out.append(cur)
    return "; ".join(f"{a:.1f}-{b:.1f} ({min(f):.1f}-{max(f):.1f} Hz, {m:.1e})" for a, b, f, m in out)


def main(out, dirs, extend=False):
    L = ["| run | airborne | gc / landed | skip interval | chatter after skip | chatter no skip | worst non-skipped line (Hz, ratio, RMS, window) | flagged non-skipped windows | skipped land-window worst line (Hz, ratio, RMS, window) |",
         "|" + "---|" * 9]
    for d in dirs:
        n = os.path.basename(d.rstrip("/")); r = score_run(d, extend)
        gl = "no landing" if r["gc"] is None else f"{r['gc']:.2f} / " + ("none" if r["landed"] is None else f"{r['landed']:.2f}")
        si = "-" if r["skip"] is None else f"{r['skip'][0]:.2f}-{r['skip'][1]:.2f} ({r['n_skipped']}/{r['n_win']} win)"
        fl = spans(r["flagged_kept"]) or "0"
        L.append(f"| {n} | {r['ta']:.1f}-{r['te']:.1f} | {gl} | {si} | {'CHATTER' if r['chatter'] else 'no'} | {'CHATTER' if r['chatter_noskip'] else 'no'} | {fmt(r['worst_kept'])} | {fl} | {fmt(r['worst_skip'])} |")
        print(L[-1], flush=True)
    open(out, "w").write("\n".join(L) + "\n")


if __name__ == "__main__":
    a = sys.argv[1:]
    ext = bool(a and a[0] == "--extend")
    a = a[1:] if ext else a
    main(a[0], a[1:], ext)
