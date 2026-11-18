#!/usr/bin/env python3
"""A-11 closing test: is effort.motor_rate_rms_per_s sample-rate dependent?

For each flight, recompute the motor-command derivative RMS over the metrics window
(window from metrics.json) on: raw log, log resampled to 285 Hz and 250 Hz (sample-and-hold
of the latest logged sample on a uniform grid), and a fixed-bandwidth version (raw derivative
after a 20 ms boxcar mean, first null 50 Hz, on uniform 800 and 250 Hz grids).
Self-test: --selftest checks that a sinusoid gives the known derivative RMS at every rate.
"""
import json, sys, glob, os
import numpy as np


def drms(t, u):
    dt = np.diff(t); g = dt > 0
    du = np.diff(u, axis=0)[g] / dt[g, None]
    return float(np.sqrt(np.mean(du ** 2)))


def resample(t, u, fs):
    tg = np.arange(t[0], t[-1], 1.0 / fs)
    i = np.searchsorted(t, tg, side="right") - 1
    return tg, u[i]


def lowpass(tg, u, width_s):
    """Boxcar mean over a fixed time width (first null at 1/width_s), valid part only."""
    n = max(1, int(round(width_s / np.median(np.diff(tg)))))
    k = np.ones(n) / n
    return tg[n - 1:], np.column_stack([np.convolve(u[:, j], k, mode="valid") for j in range(u.shape[1])])


def variants(t, u):
    out = {"raw": drms(t, u)}
    for fs in (285.0, 250.0):
        out[f"zoh_{int(fs)}"] = drms(*resample(t, u, fs))
    tg, ug = resample(t, u, 800.0)
    out["box20ms_800"] = drms(*lowpass(tg, ug, 0.02))
    tg, ug = resample(t, u, 250.0)
    out["box20ms_250"] = drms(*lowpass(tg, ug, 0.02))
    return out


def selftest():
    f, A = 5.0, 0.1  # derivative RMS = A*2*pi*f/sqrt(2)
    t = np.arange(0, 10, 1 / 800.0)
    u = (A * np.sin(2 * np.pi * f * t))[:, None]
    exp = A * 2 * np.pi * f / np.sqrt(2)
    v = variants(t, u)
    for k, x in v.items():
        assert abs(x / exp - 1) < 0.05, (k, x, exp)
    print("selftest ok", {k: round(x / exp, 4) for k, x in v.items()})


def run(d):
    from pyulog import ULog
    met = json.load(open(os.path.join(d, "metrics.json")))
    if "window" not in met:  # K113 MINOR 6: aborted run, no scored window
        print(f"{d}: skipped, metrics.json has no window (aborted run)")
        return None
    w = met["window"]
    ul = ULog(os.path.join(d, "flight.ulg"), ["actuator_motors"])
    am = ul.get_dataset("actuator_motors").data
    t = am["timestamp"] * 1e-6
    u = np.column_stack([am[f"control[{i}]"] for i in range(4)])
    m = (t >= w["start_s"]) & (t <= w["end_s"])
    r = variants(t[m], u[m])
    r["rate_hz"] = float(1 / np.median(np.diff(t[m])))
    return r


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        selftest(); sys.exit(0)
    res = {}
    for root in sys.argv[1:]:
        for d in sorted(glob.glob(os.path.join(root, "*", "r*"))):
            if os.path.exists(os.path.join(d, "flight.ulg")):
                res[d] = run(d)
                if res[d] is not None:
                    print(d, {k: round(v, 4) for k, v in res[d].items()})
    json.dump(res, open("results/a11_effort_rate.json", "w"), indent=1)
