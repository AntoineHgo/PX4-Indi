#!/usr/bin/env python3
"""Key 2, G4 PID guard (Q20, GATES.md Owner amendments S187). Written from the rule text and the raw logs.

Signal: actuator_motors control[0..3] over the airborne span (as g4_chatter_skip_key2.load), detrended per window (mean).
Windows: K.psd_windows(..., rms_hz=0.5): 4 s Hann, 1 s hop, peak bin 20-100 Hz, RMS over peak +-2 bins; ratio = peak/band median.
Transition c = each vehicle_status nav_state change inside the airborne span. Skipped windows: ta < c+3 and ta+4 > c.
Checked = some INDI skipped window of the transition (any motor) has ratio > 20 and narrow RMS >= 5e-4.
Checked -> FAIL if PID has no window (any motor, same transition) with ratio > 20 within +-0.5 Hz of the INDI peak,
or INDI narrow RMS > 1e-3; else PASS. INDI value = flagged window of largest RMS (else largest-RMS skipped window).
PID transition = same ordinal nav change inside its airborne span (nav state pair must match, else matched by pair).
Usage: g4_guard_q20_key2.py --selftest | indi_dir[,pid_dir] ...   (pid_dir '-' or absent: no reference)
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import g3_checks_key2 as K

NAV_S, RATIO, FLOOR, UPPER, TOL_HZ = 3.0, 20.0, 5e-4, 1e-3, 0.5

def skipped_windows(t, u, c):
    """Per-motor list of (ta, f, ratio, rms) for the 4 s windows overlapping [c, c+3] (rule: ta < c+3 and ta+4 > c)."""
    tg, g = K.grid(t, u); out = []
    for m in range(4):
        w = K.psd_windows(g[:, m], K.FS, 20, 100, rms_hz=0.5, t_off=tg[0])
        for x in w:
            ta = tg[0] + x[0]
            if ta < c + NAV_S and ta + 4.0 > c: out.append((ta, x[1], x[2], x[3], m))
    return out

def indi_peak(ws):
    fl = [x for x in ws if x[2] > RATIO and x[3] >= FLOOR]
    if fl: return True, max(fl, key=lambda x: x[3])
    return False, max(ws, key=lambda x: x[3])

def decide(i_checked, i, pid_ws):
    """i = INDI (ta,f,ratio,rms,motor); pid_ws = PID skipped windows or None. -> (verdict, pid_best)"""
    if not i_checked: return "not checked", (max(pid_ws, key=lambda x: x[3]) if pid_ws else None)
    if pid_ws is None: return "FAIL (no PID reference)", None
    sh = [x for x in pid_ws if x[2] > RATIO and abs(x[1] - i[1]) <= TOL_HZ]
    pb = max(sh, key=lambda x: x[3]) if sh else max(pid_ws, key=lambda x: x[3])
    if not sh: return "FAIL (INDI-only line)", pb
    if i[3] > UPPER: return "FAIL (INDI RMS > 1e-3)", pb
    return "PASS (shared)", pb

def load(d):
    from pyulog import ULog
    u = ULog(os.path.join(d, "flight.ulg"), message_name_filter_list=["sim_ground_truth", "actuator_motors", "vehicle_status"])
    D = {x.name: x.data for x in u.data_list}; g = D["sim_ground_truth"]; t = g["timestamp"] * 1e-6
    pos = np.stack([g["x"], g["y"], g["z"]], 1); z0 = np.median(pos[:800, 2])
    ev = [e for e in json.load(open(os.path.join(d, "run.json")))["events"] if e["name"] == "hold"][0]
    h0, h1 = ev["t_us"] * 1e-6, ev["t_us"] * 1e-6 + ev["dur_s"]
    sgn = 1.0 if np.median(pos[(t > h0) & (t < h1), 2]) > z0 else -1.0
    h = sgn * (pos[:, 2] - z0)
    ia = np.where(h > h[:800].mean() + 0.3)[0]; a0, a1 = t[ia[0]], t[ia[-1]]
    mo = D["actuator_motors"]; mt = mo["timestamp"] * 1e-6; mm = (mt >= a0) & (mt <= a1)
    u4 = np.stack([mo[f"control[{i}]"] for i in range(4)], 1)[mm]
    vs = D["vehicle_status"]; ns = vs["nav_state"]; vt = vs["timestamp"] * 1e-6
    ch = [(float(vt[i]), int(ns[i - 1]), int(ns[i])) for i in range(1, len(ns)) if ns[i] != ns[i - 1] and a0 <= vt[i] <= a1]
    return mt[mm], u4, ch

def run_pair(indi, pid):
    ti, ui, ci = load(indi)
    tp = up = cp = None
    if pid: tp, up, cp = load(pid)
    rows = []
    for k, (c, a, b) in enumerate(ci):
        ws = skipped_windows(ti, ui, c); ck, i = indi_peak(ws)
        pw = None
        if pid:
            m = [x for x in cp if (x[1], x[2]) == (a, b)]
            cand = cp[k] if k < len(cp) and (cp[k][1], cp[k][2]) == (a, b) else (m[0] if m else None)
            pw = skipped_windows(tp, up, cand[0]) if cand else None
        v, pb = decide(ck, i, pw)
        rows.append({"run": os.path.basename(indi.rstrip("/")), "c": c, "nav": f"{a}->{b}", "i": i, "checked": ck, "pid": pb, "verdict": v,
                     "pid_ref": bool(pid)})
    return rows

# ---- synthetic self-test -----------------------------------------------------------------------------------------------
def _sig(lines, T=60.0, seed=0):
    t = np.arange(0, T, 1 / K.FS); rng = np.random.default_rng(seed)
    u = 0.14 + rng.normal(0, 2e-5, (len(t), 4))
    for f, rms, t0, t1 in lines:
        on = (t >= t0) & (t < t1); u[on, 1] += rms * np.sqrt(2) * np.sin(2 * np.pi * f * t[on])
    return t, u

def self_test():
    ok = True
    def chk(n, got, want):
        nonlocal ok; g = got == want; ok &= g; print(("PASS " if g else "FAIL ") + n, "got", got, "want", want)
    c = 30.0
    def one(i_lines, p_lines):
        ti, ui = _sig(i_lines); ck, i = indi_peak(skipped_windows(ti, ui, c))
        tp, up = _sig(p_lines, seed=1); pw = skipped_windows(tp, up, c)
        return ck, i, decide(ck, i, pw)[0]
    ck, i, v = one([(20.0, 8e-4, 25, 40)], [(20.0, 8e-4, 25, 40)])
    chk("RMS recovered within 5 % (8e-4)", abs(i[3] - 8e-4) / 8e-4 < 0.05, True)
    chk("INDI peak 20 Hz", abs(i[1] - 20.0) <= 0.25, True)
    chk("shared line -> PASS", v, "PASS (shared)")
    ck, i, v = one([(20.0, 8e-4, 25, 40)], [])
    chk("INDI-only line -> FAIL", v, "FAIL (INDI-only line)")
    ck, i, v = one([(20.0, 8e-4, 25, 40)], [(24.0, 8e-4, 25, 40)])
    chk("PID line 4 Hz away -> FAIL", v, "FAIL (INDI-only line)")
    ck, i, v = one([(20.0, 1.5e-3, 25, 40)], [(20.0, 3e-3, 25, 40)])
    chk("INDI RMS 1.5e-3 -> FAIL", v, "FAIL (INDI RMS > 1e-3)")
    chk("INDI RMS recovered 1.5e-3 within 5 %", abs(i[3] - 1.5e-3) / 1.5e-3 < 0.05, True)
    ck, i, v = one([(20.0, 3e-4, 25, 40)], [])
    chk("below floor -> not checked", (ck, v), (False, "not checked"))
    ck, i, v = one([(20.0, 8e-4, 40, 55)], [])   # line starts at 40: windows ta<33 end by 37 -> none overlapping... ta+4>40 needs ta>36: not skipped
    chk("line outside skipped windows -> not checked", ck, False)
    return ok

if __name__ == "__main__":
    a = sys.argv[1:]
    if "--selftest" in a: sys.exit(0 if self_test() else 1)
    for arg in a:
        ind, _, pid = arg.partition(",")
        for r in run_pair(ind, pid if pid not in ("", "-") else None): print(json.dumps(r, default=float))
