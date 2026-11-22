#!/usr/bin/env python3
"""G5.5 horizontal trajectory limit (Q25 B, GATES.md "Owner amendments S197", DECISIONS.md D-OWNER-Q25).

  H_lim = max(0.5 m, TAU_ATT * v_rms),  TAU_ATT = 1 / MC_ROLL_P = 1 / 8.0 = 0.125 s,
  v_rms = RMS over the scored samples of the analytic reference horizontal speed.

The reference position is metrics.analytic_reference (the key-1 scorer's function); the speed is its central difference
(h = 1e-3 s, as run_scenario.traj_pva). Samples: the ULog truth timestamps in the scorer window [t0, t0 + dur_s)
(key 1) or [t0, t0 + dur_s] (key 2), t0 = run.json trajectory t0_us. Nothing here reads a score.

  python3 g55_traj_limit.py SCENARIO            nominal (dense uniform grid) v_rms and H_lim
  python3 g55_traj_limit.py --run RUN_DIR       v_rms and H_lim on that flight's own sample grid
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import metrics  # noqa: E402

H_FLOOR = 0.5
TAU_ATT = 1.0 / 8.0
HDIFF = 1e-3


def ref_hspeed(traj, ts_s):
    """Analytic reference horizontal speed [m/s] at times ts_s (s since trajectory start); central difference of
    metrics.analytic_reference (origin t0_us = 0, hold position 0)."""
    ts = np.asarray(ts_s, float)
    zero = np.zeros(3)
    p1 = metrics.analytic_reference(traj, 0.0, zero, (ts + HDIFF) * 1e6)
    p0 = metrics.analytic_reference(traj, 0.0, zero, (ts - HDIFF) * 1e6)
    v = (p1 - p0) / (2 * HDIFF)
    return np.hypot(v[:, 0], v[:, 1])


def v_rms(traj, ts_s):
    v = ref_hspeed(traj, ts_s)
    return float(np.sqrt(np.mean(v ** 2)))


def h_lim(vrms):
    return max(H_FLOOR, TAU_ATT * vrms)


def window_times(t_s, t0_s, dur_s, closed=False):
    """Scorer sample selection: truth times t_s in [t0, t0 + dur) (key 1) or [t0, t0 + dur] (key 2), as time since t0."""
    t_s = np.asarray(t_s, float)
    m = (t_s >= t0_s) & ((t_s <= t0_s + dur_s) if closed else (t_s < t0_s + dur_s))
    return t_s[m] - t0_s


def nominal_grid(traj, dt=0.005):
    dur = metrics_dur(traj)
    return np.arange(0.0, dur, dt)


def metrics_dur(traj):
    import math
    return 2 * math.pi * traj["laps"] / traj["w"] + traj["ramp_s"]


def run_vrms(run_dir):
    """(v_rms key 1, v_rms key 2, n1, n2) for one flight dir on its own truth sample grid."""
    from pyulog import ULog
    run = json.load(open(os.path.join(run_dir, "run.json")))
    u = ULog(os.path.join(run_dir, "flight.ulg"))
    gt, _ = metrics.truth_local_position(u)
    tr = run["trajectory"]
    ev = {e["name"]: e for e in run["events"]}
    t = gt["timestamp"] * 1e-6
    out = []
    # key 1 window starts at the "traj" event, key 2 at trajectory t0_us (equal in the FREEZE-10 flights)
    for t0, closed in ((ev["traj"]["t_us"] * 1e-6, False), (tr["t0_us"] * 1e-6, True)):
        ts = window_times(t, t0, tr["dur_s"] if closed else ev["traj"]["dur_s"], closed)
        # reference time origin is trajectory t0 in both keys
        ts = ts + (t0 - tr["t0_us"] * 1e-6)
        out.append((v_rms(tr, ts), len(ts)))
    return out[0][0], out[1][0], out[0][1], out[1][1]


def main():
    import scenarios
    a = sys.argv[1:]
    if a and a[0] == "--run":
        v1, v2, n1, n2 = run_vrms(a[1])
        print(f"{a[1]}: v_rms key1 {v1:.4f} (n {n1}) key2 {v2:.4f} (n {n2}) H_lim {h_lim(v1):.4f} m")
        return 0
    names = a or [k for k in scenarios.SCENARIOS if k[:2] in ("o1", "o2", "o3", "o4", "o5", "o6", "o7")]
    for n in names:
        v = v_rms(scenarios.SCENARIOS[n]["traj"], nominal_grid(scenarios.SCENARIOS[n]["traj"]))
        print(f"{n:24s} v_rms {v:.4f} m/s  tau*v_rms {TAU_ATT * v:.4f}  H_lim {h_lim(v):.4f} m")
    return 0


if __name__ == "__main__":
    sys.exit(main())
