#!/usr/bin/env python3
"""G4 noise/effort metrics (GATES.md G4): R20, R4 (true rotor speed), C20, C4 (motor command), clip fraction.

R = RMS of (x - lowpass(x)), per motor, mean over motors; rad/s and % of the window-mean speed (hover).
Filter: 4th-order Butterworth, zero phase (filtfilt), on a uniform grid (linear interpolation at the median logged rate
of the topic); 2 s dropped at each window edge after filtering. Time base: log start, as in vib_line_check.py.
True rotor speed: esc_status.esc[i].esc_rpm, which the gz_bridge fills from the Gazebo joint velocity (SIM_GZ_ESC_FB=1,
rounded to 1 rpm), NOT the eRPM telemetry model (mode 2: latency, 100 eRPM rounding, drops). Under mode 2 the
gz_bridge publishes the truth on esc_status instance 1 (hook 10c741af4b), instance 0 being the telemetry model.
The mode is read from the log parameters and reported as esc_fb; the instance is chosen from it (FB=1 -> 0, FB=2 -> 1)
unless --esc-instance is given; truth = (FB 1, inst 0) or (FB 2, inst 1), otherwise the R values are a PROXY. Time stamps: timestamp_sample if the topic has it, else
timestamp (esc_status has no timestamp_sample; actuator_motors does). Never mixed within a topic.

Usage: g4_metrics.py LOG.ulg --t0 S --t1 S [--json PATH]   |   g4_metrics.py --selftest
"""
import argparse
import json
import sys

import numpy as np

EDGE_S = 2.0
CLIP_TOL = 1e-4


def uniform(t, x, t0, t1):
    """Resample x(t) (n,) or (n,m) to the median logged rate inside [t0, t1]; returns (tg, xg, fs)."""
    m = (t >= t0) & (t <= t1)
    t, x = t[m], x[m]
    fs = 1.0 / np.median(np.diff(t))
    tg = np.arange(t[0], t[-1], 1.0 / fs)
    xg = np.array([np.interp(tg, t, c) for c in np.atleast_2d(x.T)])  # (m, n)
    return tg, xg, fs


def hf_rms(xg, fs, fc, edge=EDGE_S):
    """RMS of (x - lowpass_fc(x)) per row, edges dropped after filtering."""
    from scipy.signal import butter, filtfilt
    b, a = butter(4, fc / (fs / 2.0))
    lp = filtfilt(b, a, xg, axis=-1)
    k = int(round(edge * fs))
    r = (xg - lp)[:, k:-k]
    return np.sqrt(np.mean(r ** 2, axis=-1))


def metrics_from(t_rpm, rpm, t_cmd, cmd, t0, t1, fc_hi=20.0, fc_lo=4.0):
    """rpm (n,4) in rpm, cmd (n,4) in 0-1; times in s. Returns dict."""
    tg, w, fs_r = uniform(t_rpm, rpm * (2 * np.pi / 60.0), t0, t1)
    hover = float(np.mean(w[:, int(EDGE_S * fs_r):-int(EDGE_S * fs_r)]))
    out = {"window_s": [t0, t1], "rotor_rate_hz": fs_r, "hover_speed_rad_s": hover}
    for name, fc in (("R20", fc_hi), ("R4", fc_lo)):
        v = hf_rms(w, fs_r, fc)
        out[name] = {"per_motor_rad_s": v.tolist(), "mean_rad_s": float(v.mean()), "mean_pct_hover": float(100 * v.mean() / hover)}
    tc, c, fs_c = uniform(t_cmd, cmd, t0, t1)
    out["cmd_rate_hz"] = fs_c
    for name, fc in (("C20", fc_hi), ("C4", fc_lo)):
        v = hf_rms(c, fs_c, fc)
        out[name] = {"per_motor": v.tolist(), "mean": float(v.mean())}
    m = (t_cmd >= t0) & (t_cmd <= t1)
    cc = cmd[m]
    out["clip_fraction"] = float(np.mean((cc <= CLIP_TOL) | (cc >= 1 - CLIP_TOL)))
    return out


def selftest(fc_hi=20.0):
    rng = np.random.default_rng(1)
    ok = True

    def chk(label, val, exp, tol=0.03, absolute=None):
        nonlocal ok
        good = abs(val - exp) <= (absolute if absolute is not None else tol * abs(exp))
        ok &= good
        print(f"selftest {label}: got {val:.5g} expected {exp:.5g} {'OK' if good else 'FAIL'}")

    # irregular sample times: jittered 1 kHz rpm and command (linear interpolation loses a few % of a 50 Hz line at lower rates), 60 s
    def times(rate, n):
        return np.cumsum(np.full(n, 1.0 / rate) * (1 + 0.2 * rng.uniform(-1, 1, n)))
    tr, tc = times(1000, 60000), times(1000, 60000)
    A, base = 20.0, 1300.0  # rpm-domain amplitude below converted
    Aw = A * 2 * np.pi / 60
    k = 2 * np.pi
    for label, f1amp in (("50Hz only", 0.0), ("50Hz + 8Hz", 30.0)):
        rpm = base + A * np.sin(k * 50 * tr)[:, None] * np.ones(4) + (f1amp * np.sin(k * 8 * tr))[:, None]
        cmd = 0.5 + 0.01 * np.sin(k * 50 * tc)[:, None] * np.ones(4) + (0.1 * f1amp / 30.0) * np.sin(k * 8 * tc)[:, None]
        r = metrics_from(tr, rpm, tc, cmd, 5, 55, fc_hi=fc_hi)
        chk(f"R20 {label}", r["R20"]["mean_rad_s"], Aw / np.sqrt(2))
        chk(f"C20 {label}", r["C20"]["mean"], 0.01 / np.sqrt(2))
        if f1amp:
            A1 = f1amp * 2 * np.pi / 60
            exp4 = np.sqrt((Aw ** 2 + A1 ** 2) / 2)
            chk(f"R4 {label} (contains 8 Hz)", r["R4"]["mean_rad_s"], exp4)
            chk(f"C4 {label} (contains 8 Hz)", r["C4"]["mean"], np.sqrt((0.01 ** 2 + 0.1 ** 2) / 2))
        else:
            chk(f"R4 {label}", r["R4"]["mean_rad_s"], Aw / np.sqrt(2))
    # clipped command: 10 % of samples at 0, 5 % at 1 -> 0.15 exactly known
    n = len(tc)
    cmd = np.full((n, 4), 0.5)
    cmd[: n // 10] = 0.0
    cmd[n // 10: n // 10 + n // 20] = 1.0
    tcs = np.arange(n) / 1000.0
    r = metrics_from(tr, np.full((len(tr), 4), base), tcs, cmd, 0, tcs[-1])
    chk("clip fraction", r["clip_fraction"], (n // 10 + n // 20) / n, absolute=2e-3)
    print("selftest", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log", nargs="?")
    ap.add_argument("--t0", type=float)
    ap.add_argument("--t1", type=float)
    ap.add_argument("--json")
    ap.add_argument("--esc-instance", type=int, help="esc_status multi-instance (default: 1 if SIM_GZ_ESC_FB=2 else 0)")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--break-check", action="store_true", help="selftest with a 200 Hz cutoff: must FAIL")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.break_check:
        rc = selftest(fc_hi=200.0)
        print("break-check", "OK (selftest failed as required)" if rc else "BAD (selftest passed with 200 Hz)")
        return 0 if rc else 1
    from pyulog import ULog
    u = ULog(a.log, ["esc_status", "actuator_motors"])
    t_start = u.start_timestamp
    fb = u.initial_parameters.get("SIM_GZ_ESC_FB")
    inst = a.esc_instance if a.esc_instance is not None else (1 if fb == 2 else 0)
    esc = u.get_dataset("esc_status", inst).data
    am = u.get_dataset("actuator_motors").data
    key_e = "timestamp_sample" if "timestamp_sample" in esc else "timestamp"
    key_c = "timestamp_sample" if "timestamp_sample" in am else "timestamp"
    te = (esc[key_e].astype(np.int64) - t_start) * 1e-6
    tc = (am[key_c].astype(np.int64) - t_start) * 1e-6
    rpm = np.stack([np.abs(esc[f"esc[{i}].esc_rpm"]).astype(float) for i in range(4)], axis=1)
    cmd = np.stack([am[f"control[{i}]"] for i in range(4)], axis=1)
    r = metrics_from(te, rpm, tc, cmd, a.t0, a.t1)
    r.update(log=a.log, rotor_topic=f"esc_status[{inst}].esc[i].esc_rpm (time: {key_e})", cmd_topic=f"actuator_motors.control[0..3] (time: {key_c})")
    r["esc_fb"] = fb
    r["esc_instance"] = inst
    r["rotor_speed_is_truth"] = (fb, inst) in ((1, 0), (2, 1))
    if not r["rotor_speed_is_truth"]:
        print(f"WARNING: SIM_GZ_ESC_FB={fb}, instance {inst}: esc_rpm is not simulator truth, R20/R4 are a proxy", file=sys.stderr)
    s = json.dumps(r, indent=1)
    if a.json:
        open(a.json, "w").write(s + "\n")
    print(s)
    return 0


if __name__ == "__main__":
    sys.exit(main())
