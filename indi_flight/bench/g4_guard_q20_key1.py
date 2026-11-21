#!/usr/bin/env python3
"""G4 PID guard, Q20 rule (GATES.md 'Owner amendments S187'), key 1.
Usage (repo root): g4_guard_q20_key1.py <indi run dir>...   (PID ref = sibling g4_pid/<same name>, if present)
       g4_guard_q20_key1.py --selftest
Per nav_state change c inside the airborne span (h > start+0.3 m, as guard_q19.py), skipped windows = 4 s Hann windows (hop 1 s)
with ta < c+3 and ta+4 > c, all 4 motors, narrow-band measure psd_windows(..., rms_hz=0.5) (peak bin 20-100 Hz, RMS peak +-2 bins).
Flagged = ratio > 20 and narrow RMS >= 5e-4. Transition checked only if an INDI skipped window is flagged (INDI peak = flagged window of max RMS).
Checked: FAIL if no PID window (any motor, same transition, skipped) with ratio > 20 within +-0.5 Hz of the INDI peak, or INDI RMS > 1e-3; else PASS.
Rows: INDI/PID values come from the max-narrow-RMS skipped window (checked: INDI flagged window, PID = best matching window if any)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import g3_checks_key2 as K

RATIO, FLOOR, CAP, HZTOL = 20.0, 5e-4, 1e-3, 0.5

def skipped_windows(W, t0, c):
    """W: per-motor psd_windows lists; t0: absolute time of grid start. -> [(motor, ta, f, ratio, rms)] overlapping [c, c+3]."""
    return [(i, t0 + w[0], w[1], w[2], w[3]) for i in range(len(W)) for w in W[i]
            if t0 + w[0] < c + K.NAV_SKIP_S and t0 + w[0] + 4.0 > c]

def verdict(indi, pid):
    """indi, pid: skipped-window lists (pid None = no reference). -> dict."""
    flg = [w for w in indi if w[3] > RATIO and w[4] >= FLOOR]
    ib = max(flg or indi, key=lambda w: w[4], default=None)
    r = {"indi": ib, "checked": bool(flg), "pid": None, "verdict": "not checked"}
    if pid:
        if flg:
            m = [w for w in pid if w[3] > RATIO and abs(w[2] - ib[2]) <= HZTOL]
            r["pid"] = max(m, key=lambda w: w[4]) if m else max(pid, key=lambda w: w[4])
        else:
            r["pid"] = max(pid, key=lambda w: w[4])
    if flg:
        if ib[4] > CAP: r["verdict"] = "FAIL (INDI RMS > 1e-3)"
        elif not pid or not (r["pid"][3] > RATIO and abs(r["pid"][2] - ib[2]) <= HZTOL): r["verdict"] = "FAIL (INDI-only line)"
        else: r["verdict"] = "PASS (shared transient)"
    return r

def load(d):
    from pyulog import ULog
    u = ULog(os.path.join(d, "flight.ulg"), message_name_filter_list=["sim_ground_truth", "actuator_motors", "vehicle_status"])
    D = {x.name: x.data for x in u.data_list}; g = D["sim_ground_truth"]; t = g["timestamp"] * 1e-6
    pos = np.stack([g["x"], g["y"], g["z"]], 1); z0 = np.median(pos[:800, 2])
    ev = [e for e in json.load(open(os.path.join(d, "run.json")))["events"] if e["name"] == "hold"][0]
    h0, h1 = ev["t_us"] * 1e-6, ev["t_us"] * 1e-6 + ev["dur_s"]
    sgn = 1.0 if np.median(pos[(t > h0) & (t < h1), 2]) > z0 else -1.0
    h = sgn * (pos[:, 2] - z0); ia = np.where(h > h[:800].mean() + 0.3)[0]; a0, a1 = t[ia[0]], t[ia[-1]]
    mo = D["actuator_motors"]; mt = mo["timestamp"] * 1e-6; mm = (mt >= a0) & (mt <= a1)
    uu = np.stack([mo[f"control[{i}]"] for i in range(4)], 1)[mm]
    tg, gr = K.grid(mt[mm], uu)
    W = [K.psd_windows(gr[:, i], K.FS, 20, 100, rms_hz=0.5, t_off=tg[0]) for i in range(4)]
    vs = D["vehicle_status"]; ns = vs["nav_state"]; vt = vs["timestamp"] * 1e-6
    cnt = {}; tr = {}
    for j in np.flatnonzero(np.diff(ns) != 0) + 1:
        c = float(vt[j]); p = f"{int(ns[j-1])}->{int(ns[j])}"; cnt[p] = cnt.get(p, 0) + 1
        if a0 <= c <= a1: tr[f"{p}#{cnt[p]}"] = skipped_windows(W, tg[0], c)
    return tr

def fmt(w, k):
    return ("-", "-", "-") if w is None else (f"{w[2]:.2f}", f"{w[4]:.2e}", f"{w[3]:.1f}")

def main(dirs):
    rows = []; nchk = nfail = 0; mx = (0.0, "")
    print("| run | transition | INDI peak Hz | INDI narrow RMS | INDI ratio | checked | PID peak Hz | PID narrow RMS | PID ratio | verdict |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for d in dirs:
        name = os.path.basename(d.rstrip("/")); pd_ = os.path.join(os.path.dirname(d.rstrip("/")), "..", "g4_pid", name)
        pd_ = os.path.normpath(pd_); ti = load(d); tp = load(pd_) if os.path.exists(os.path.join(pd_, "flight.ulg")) else None
        for tid, iw in ti.items():
            r = verdict(iw, None if tp is None else tp.get(tid, []))
            ib = r["indi"]
            if ib and ib[4] > mx[0]: mx = (ib[4], f"{name} {tid}")
            nchk += r["checked"]; nfail += r["verdict"].startswith("FAIL")
            a, b, c = fmt(ib, 0); e, f_, g = fmt(r["pid"], 0)
            pidnote = "" if tp is not None else " (no PID ref)"
            print(f"| {name} | {tid} | {a} | {b} | {c} | {'yes' if r['checked'] else 'no'} | {e} | {f_} | {g} | {r['verdict']}{pidnote} |", flush=True)
    print(f"max INDI narrow RMS over skipped windows: {mx[0]:.3e} ({mx[1]})")
    print(f"guard: {nchk} checked, {nfail} FAIL")

def selftest():
    fs = K.FS; T = 60.0; t = np.arange(int(T * fs)) / fs; c = 30.0
    def sig(f, rms, seed):
        rng = np.random.default_rng(seed); x = 1e-4 * rng.standard_normal(t.size)
        return x + (np.sqrt(2) * rms * np.sin(2 * np.pi * f * t) if rms else 0)
    def win(x): return skipped_windows([K.psd_windows(x, fs, 20, 100, rms_hz=0.5)], 0.0, c)
    ok = True
    def chk(n, cond):
        nonlocal ok; ok &= bool(cond); print(("PASS " if cond else "FAIL ") + n)
    iw = win(sig(20.0, 7e-4, 1)); b = max(iw, key=lambda w: w[4])
    chk(f"known 20 Hz line rms 7e-4 measured {b[4]:.3e} at {b[2]} Hz", abs(b[4] / 7e-4 - 1) < 0.05 and b[2] == 20.0 and b[3] > RATIO)
    chk("n skipped windows = 6 (c-4..c+3 starts, excl. bounds)", len(iw) == 6)
    r = verdict(iw, win(sig(0, 0, 2))); chk("INDI-only line -> FAIL", r["checked"] and r["verdict"].startswith("FAIL (INDI-only"))
    r = verdict(iw, win(sig(20.3, 6e-4, 3))); chk("shared line (PID 20.3 Hz) -> PASS", r["checked"] and r["verdict"].startswith("PASS"))
    r = verdict(iw, win(sig(25.0, 6e-4, 3))); chk("PID line 5 Hz away -> FAIL", r["verdict"].startswith("FAIL (INDI-only"))
    r = verdict(win(sig(20.0, 1.2e-3, 4)), win(sig(20.0, 1.2e-3, 5))); chk("INDI 1.2e-3 with shared PID line -> FAIL", r["verdict"].startswith("FAIL (INDI RMS"))
    r = verdict(win(sig(20.0, 3e-4, 6)), win(sig(0, 0, 7))); chk("below-floor line 3e-4 -> not checked", not r["checked"] and r["verdict"] == "not checked")
    r = verdict(win(sig(0, 0, 8)), None); chk("no line, no PID ref -> not checked", r["verdict"] == "not checked")
    print("selftest", "OK" if ok else "FAILED"); return 0 if ok else 1

if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]: sys.exit(selftest())
    main(sys.argv[1:])
