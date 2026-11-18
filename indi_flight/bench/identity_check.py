#!/usr/bin/env python3
"""Identity check: does a configuration change alter the flight beyond run-to-run spread?

Compares hover statistics of runs (truth position, motor commands) over the last
WINDOW seconds of the log. Prints one row per run and the max pairwise difference
inside the reference group and between groups.

Usage: identity_check.py --ref run_a run_b --test run_c [--window 40]
"""
import argparse
import itertools

import numpy as np


def stats_from_arrays(t_us, z, x, y, motors, window_s, t_end_us=None):
    """Hover statistics over the window_s seconds ending at t_end_us (default: end of each array)."""
    out = {}
    tp = t_us[0]
    te = tp[-1] if t_end_us is None else t_end_us
    m = (tp >= te - window_s * 1e6) & (tp <= te)
    out["z_std_m"] = float(np.std(z[m]))
    out["xy_std_m"] = float(np.hypot(np.std(x[m]), np.std(y[m])))
    tm, u = t_us[1], motors
    te = tm[-1] if t_end_us is None else t_end_us
    mm = (tm >= te - window_s * 1e6) & (tm <= te)
    out["u_mean"] = float(np.mean(u[mm]))
    out["u_rms_ac"] = float(np.sqrt(np.mean((u[mm] - u[mm].mean(axis=0)) ** 2)))
    return out


def run_stats(run_dir, window_s):
    """Window ends at the end of the run's 'hold' event (run.json, PX4 time), so landing is excluded."""
    import json
    from pyulog import ULog
    ev = [e for e in json.load(open(f"{run_dir}/run.json"))["events"] if e["name"] == "hold"][0]
    t_end = ev["t_us"] + ev["dur_s"] * 1e6
    ulog = ULog(f"{run_dir}/flight.ulg", ["vehicle_local_position_groundtruth", "actuator_motors"])
    lp = ulog.get_dataset("vehicle_local_position_groundtruth").data
    am = ulog.get_dataset("actuator_motors").data
    u = np.column_stack([am[f"control[{i}]"] for i in range(4)])
    return stats_from_arrays((lp["timestamp"], am["timestamp"]), lp["z"], lp["x"], lp["y"], u, window_s, t_end)


def max_rel_diff(a, b):
    return {k: abs(a[k] - b[k]) / max(abs(a[k]), abs(b[k]), 1e-12) for k in a}


def self_test():
    t = np.arange(0, 60e6, 2500.0)
    rng = np.random.default_rng(0)
    z = 0.01 * rng.standard_normal(t.size)
    u = 0.4 + 0.01 * rng.standard_normal((t.size, 4))
    s = stats_from_arrays((t, t), z, z, z, u, 40)
    assert abs(s["z_std_m"] - 0.01) < 1e-3, s
    assert abs(s["u_mean"] - 0.4) < 1e-3, s
    assert abs(s["u_rms_ac"] - 0.01) < 1e-3, s
    d = max_rel_diff(s, dict(s, u_mean=0.44))
    assert abs(d["u_mean"] - (0.44 - s["u_mean"]) / 0.44) < 1e-9
    assert d["z_std_m"] == 0.0
    print("self-test OK")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", nargs="+")
    ap.add_argument("--test", nargs="+")
    ap.add_argument("--window", type=float, default=40.0)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        self_test()
        return
    st = {r: run_stats(r, a.window) for r in a.ref + a.test}
    for r, s in st.items():
        print(r, {k: round(v, 5) for k, v in s.items()})
    within = {}
    for p, q in itertools.combinations(a.ref, 2):
        for k, v in max_rel_diff(st[p], st[q]).items():
            within[k] = max(within.get(k, 0.0), v)
    between = {}
    for p in a.ref:
        for q in a.test:
            for k, v in max_rel_diff(st[p], st[q]).items():
                between[k] = max(between.get(k, 0.0), v)
    print("max rel diff within ref:", {k: round(v, 4) for k, v in within.items()})
    print("max rel diff ref vs test:", {k: round(v, 4) for k, v in between.items()})


if __name__ == "__main__":
    main()
