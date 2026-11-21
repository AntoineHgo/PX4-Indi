#!/usr/bin/env python3
"""Gate G4 noise/effort metrics, independent second implementation (key 2).

R20/R4: RMS of (x - lowpass(x)) for the true rotor speed [rad/s]; C20/C4 same
for actuator_motors.control[0..3]. Clip fraction on command samples.
"""
import argparse, json, sys
import numpy as np
from scipy.signal import butter, sosfiltfilt

EDGE_S = 2.0


def uniform_grid(t, y, t0, t1):
    """Resample y(t) (t sorted, may be jittered) on the median-rate grid over [t0,t1]."""
    dt = np.median(np.diff(t))
    n = int(np.floor((t1 - t0) / dt)) + 1
    g = t0 + dt * np.arange(n)
    return g, np.column_stack([np.interp(g, t, y[:, k]) for k in range(y.shape[1])]), 1.0 / dt


def hp_rms(t, y, t0, t1, fc):
    """Return per-channel RMS of x-lowpass(x), after dropping EDGE_S at each end, and window mean."""
    # use data slightly outside window for interpolation context
    g, yg, fs = uniform_grid(t, y, t0, t1)
    sos = butter(4, fc / (fs / 2.0), btype="low", output="sos")
    res = yg - sosfiltfilt(sos, yg, axis=0)
    keep = (g >= t0 + EDGE_S) & (g <= t1 - EDGE_S)
    rms = np.sqrt(np.mean(res[keep] ** 2, axis=0))
    return rms, yg.mean(axis=0), fs


def metrics(rt, rw, ct, cu, t0, t1):
    out = {}
    for tag, fc in (("20", 20.0), ("4", 4.0)):
        rms, mean, fs = hp_rms(rt, rw, t0, t1, fc)
        out["R" + tag] = float(rms.mean())
        out["R%s_pct" % tag] = float(100 * rms.mean() / mean.mean())
        out["rotor_fs_hz"] = float(fs)
        out["rotor_mean_rads"] = float(mean.mean())
        crm, _, cfs = hp_rms(ct, cu, t0, t1, fc)
        out["C" + tag] = float(crm.mean())
        out["cmd_fs_hz"] = float(cfs)
    m = (ct >= t0) & (ct <= t1)
    v = cu[m]
    out["clip_frac"] = float(np.mean((v <= 0) | (v >= 1)))
    out["n_cmd_samples"] = int(v.size)
    return out


def load(path):
    from pyulog import ULog
    u = ULog(path)
    t_start = u.start_timestamp * 1e-6
    fb = u.initial_parameters.get("SIM_GZ_ESC_FB")
    inst = 1 if fb == 2 else 0
    def ts(d):
        k = "timestamp_sample" if "timestamp_sample" in d.data else "timestamp"
        return d.data[k] * 1e-6 - t_start
    esc = [d for d in u.data_list if d.name == "esc_status" and d.multi_id == inst]
    mot = [d for d in u.data_list if d.name == "actuator_motors" and d.multi_id == 0]
    if not esc or not mot:
        sys.exit("missing esc_status inst %d or actuator_motors" % inst)
    esc, mot = esc[0], mot[0]
    rt = ts(esc)
    rw = np.column_stack([np.abs(esc.data["esc[%d].esc_rpm" % i].astype(float)) * 2 * np.pi / 60 for i in range(4)])
    ct = ts(mot)
    cu = np.column_stack([mot.data["control[%d]" % i].astype(float) for i in range(4)])
    def clean(t, y):
        t, idx = np.unique(t, return_index=True)
        return t, y[idx]
    rt, rw = clean(rt, rw); ct, cu = clean(ct, cu)
    return rt, rw, ct, cu, fb, inst


def selftest():
    rng = np.random.default_rng(3)
    A, A1, A8 = 20.0, 30.0, 15.0
    T = 30.0
    fs = 2000.0  # linear interp attenuates 50 Hz at few samples/period; real logs are fast
    n = int(T * fs)
    t = np.arange(n) / fs + rng.uniform(-0.2, 0.2, n) / fs  # jitter 20% of period
    t.sort()
    base = 1000.0
    def sig(a50, a8, a1, ph):
        return base + a50 * np.sin(2*np.pi*50*t + ph) + a8 * np.sin(2*np.pi*8*t + ph) + a1 * np.sin(2*np.pi*1*t + ph)
    rw = np.column_stack([sig(A, A8, A1, p) for p in (0, 1, 2, 3)])
    # command: 0.5 + 0.02 sin50 + 0.01 sin8 + 0.1 sin1, with a known clip fraction
    cfs = 1000.0
    ct = np.arange(int(T * cfs)) / cfs
    ct = ct + rng.uniform(-0.2, 0.2, ct.size) / cfs; ct.sort()
    cu = np.column_stack([0.5 + 0.02*np.sin(2*np.pi*50*ct+p) + 0.01*np.sin(2*np.pi*8*ct+p) + 0.1*np.sin(2*np.pi*ct+p) for p in range(4)])
    # clip: 10% of samples of motor 0 set to 1.0 and 5% of motor 1 set to 0 -> 15%/4 = 3.75%
    n0 = cu.shape[0]
    cu[:int(0.10*n0):1, 0] = 1.0
    cu[n0 - int(0.05*n0):, 1] = 0.0
    t0, t1 = 3.0, 27.0
    # expected clip fraction computed from the window
    w = (ct >= t0) & (ct <= t1)
    exp_clip = float(np.mean((cu[w] <= 0) | (cu[w] >= 1)))
    # clip regions lie outside window except none -> place analytically instead
    cu2 = cu.copy()
    # re-do: clips inside the window, exactly counted
    cu2 = cu.copy(); cu2[:] = np.column_stack([0.5 + 0.02*np.sin(2*np.pi*50*ct+p) + 0.01*np.sin(2*np.pi*8*ct+p) + 0.1*np.sin(2*np.pi*ct+p) for p in range(4)])
    iw = np.where(w)[0]
    nw = iw.size
    k0 = int(round(0.10 * nw)); k1 = int(round(0.05 * nw))
    cu2[iw[:k0], 0] = 1.0       # high clip
    cu2[iw[-k1:], 1] = -0.2     # low clip
    exp_clip = (k0 + k1) / (4.0 * nw)
    m = metrics(t, rw, ct, cu2 if False else cu2, t0, t1)
    # expectations
    e_r20 = A / np.sqrt(2)
    e_r4 = np.sqrt(A**2 + A8**2) / np.sqrt(2)
    e_r20p = 100 * e_r20 / base
    ok = True
    def chk(name, got, exp, tol):
        nonlocal ok
        good = abs(got - exp) <= tol * abs(exp)
        ok &= good
        print("%-9s got %.5g expected %.5g  %s" % (name, got, exp, "ok" if good else "BAD"))
    chk("R20", m["R20"], e_r20, 0.02)
    chk("R20_pct", m["R20_pct"], e_r20p, 0.02)
    chk("R4", m["R4"], e_r4, 0.02)
    # command signal clip regions distort C; check C only on clean motors via a separate clean call
    ccl = np.column_stack([0.5 + 0.02*np.sin(2*np.pi*50*ct+p) + 0.01*np.sin(2*np.pi*8*ct+p) + 0.1*np.sin(2*np.pi*ct+p) for p in range(4)])
    mc = metrics(t, rw, ct, ccl, t0, t1)
    chk("C20", mc["C20"], 0.02/np.sqrt(2), 0.02)
    chk("C4", mc["C4"], np.sqrt(0.02**2 + 0.01**2)/np.sqrt(2), 0.02)
    chk("clip", m["clip_frac"], exp_clip, 1e-9)
    print("clean clip (expect 0): %g" % mc["clip_frac"])
    ok &= mc["clip_frac"] == 0.0
    print("SELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log", nargs="?")
    ap.add_argument("--t0", type=float)
    ap.add_argument("--t1", type=float)
    ap.add_argument("--json")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.log is None or a.t0 is None or a.t1 is None:
        ap.error("LOG --t0 --t1 required")
    rt, rw, ct, cu, fb, inst = load(a.log)
    m = metrics(rt, rw, ct, cu, a.t0, a.t1)
    m.update(log=a.log, t0=a.t0, t1=a.t1, esc_fb=fb, esc_instance=inst)
    print("SIM_GZ_ESC_FB=%s -> esc_status instance %d; rotor fs %.1f Hz, cmd fs %.1f Hz" % (fb, inst, m["rotor_fs_hz"], m["cmd_fs_hz"]))
    print("R20 = %.4f rad/s (%.4f %%)" % (m["R20"], m["R20_pct"]))
    print("R4  = %.4f rad/s (%.4f %%)" % (m["R4"], m["R4_pct"]))
    print("C20 = %.6f" % m["C20"])
    print("C4  = %.6f" % m["C4"])
    print("clip fraction = %.6f (%d samples)" % (m["clip_frac"], m["n_cmd_samples"]))
    if a.json:
        json.dump(m, open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
