#!/usr/bin/env python3
"""Second-key trajectory tracking error from raw ULog files.

  python3 -I indi_flight/bench/second_key_traj.py --selftest
  python3 -I indi_flight/bench/second_key_traj.py RUN_DIR [RUN_DIR ...]

RUN_DIR holds run.json (trajectory, hold_pos_ned, t_window_*_us, ulog name) and the ULog file.
Reference NED position at ULog time t [us]: hold_pos_ned + traj_pos(traj_phase(t - t0)), t0 = trajectory.t0_us.
"""
import argparse
import json
import math
import os
import sys

import numpy as np

OFFBOARD = 14
TOPICS = ["vehicle_status", "vehicle_local_position", "vehicle_local_position_groundtruth"]


def traj_phase(traj, t):
    """Phase [rad] at elapsed time t [s]. Phase rate ramps 0 -> w (smoothstep over ramp_s), cruises at w, ramps back
    to 0; total phase = laps * 2 pi. Zero for t <= 0, constant after the end."""
    w, tr = traj["w"], traj["ramp_s"]
    total = 2 * math.pi * traj["laps"]
    tc = total / w - tr
    if t <= 0:
        return 0.0
    if t < tr:
        u = t / tr
        return w * tr * (u**3 - u**4 / 2)
    if t < tr + tc:
        return w * tr / 2 + w * (t - tr)
    if t < 2 * tr + tc:
        u = (2 * tr + tc - t) / tr
        return total - w * tr * (u**3 - u**4 / 2)
    return total


def traj_pos(traj, phi):
    """NED offset [m] from the hold position at phase phi."""
    s = traj["shape"]
    if s == "lemniscate":  # Gerono lemniscate, semi-axes ax (N), ay (E)
        return [traj["ax"] * math.sin(phi), traj["ay"] * math.sin(2 * phi), 0.0]
    if s == "circle":  # circle through the hold point, plus vertical sine (NED z down)
        r = traj["r"]
        return [r * (math.cos(phi) - 1.0), r * math.sin(phi), -traj["z_amp"] * math.sin(phi)]
    if s == "zmulti":  # vertical multisine, harmonic k with amplitude a [m]
        return [0.0, 0.0, -sum(a * math.sin(k * phi) for k, a in zip(traj["harm"], traj["amps"]))]
    raise ValueError(f"unknown trajectory shape {s}")


def ref_ned(traj, hold, t0_us, t_us):
    """Reference NED position (N,3) at ULog times t_us [us], evaluated exactly at each time (no interpolation)."""
    el = (np.asarray(t_us, dtype=float) - t0_us) * 1e-6
    off = np.array([traj_pos(traj, traj_phase(traj, e)) for e in el])
    return np.asarray(hold, dtype=float) + off


def score(ref, xyz, mask):
    """Error metrics [m] over samples with mask true and finite xyz."""
    ok = mask & np.all(np.isfinite(xyz), axis=1)
    if not ok.any():
        return {"n": 0}
    e = xyz[ok] - ref[ok]
    n = np.linalg.norm(e, axis=1)
    return {"n": int(ok.sum()), "rms3d": float(np.sqrt(np.mean(n**2))), "max3d": float(n.max()),
            "rmsN": float(np.sqrt(np.mean(e[:, 0]**2))), "rmsE": float(np.sqrt(np.mean(e[:, 1]**2))),
            "rmsD": float(np.sqrt(np.mean(e[:, 2]**2))), "err_first": float(n[0])}


def load_ulog(path):
    from pyulog import ULog
    ul = ULog(path, message_name_filter_list=TOPICS)
    return {n: ul.get_dataset(n).data for n in TOPICS}


def selftest():
    r, v = 2.0, 2.0  # circle radius [m], speed [m/s], phase rate w = v / r
    traj = {"shape": "circle", "r": r, "z_amp": 0.0, "w": v / r, "laps": 1, "ramp_s": 1e-3}
    hold = [0.0, 0.0, -5.0]
    t_us = np.arange(1e6, 6e6, 2e4)  # 1..6 s at 50 Hz, inside the cruise phase
    ref = ref_ned(traj, hold, 0, t_us)
    truth = ref_ned(traj, hold, 0, t_us - 1e5)  # reference delayed by 100 ms
    m = score(ref, truth, np.ones(len(t_us), bool))
    zero = score(ref, ref, np.ones(len(t_us), bool))["rms3d"]
    expect = v * 0.1
    rel = abs(m["rms3d"] - expect) / expect
    print(f"selftest: circle r={r} v={v}, truth = ref delayed 0.1 s: rms3d={m['rms3d']:.5f} m, "
          f"expected v*0.1={expect:.4f} m, rel err={rel:.2e}; zero-delay rms3d={zero:.2e}")
    return rel < 0.01 and zero < 1e-9


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="*", help="run directories holding run.json and the ULog")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    print("| run | source | scoring | n | rms3d [m] | max3d [m] | rmsN | rmsE | rmsD | err@first [m] |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for rdir in a.runs:
        meta = json.load(open(os.path.join(rdir, "run.json")))
        tr, hold, t0 = meta["trajectory"], meta["hold_pos_ned"], meta["trajectory"]["t0_us"]
        ws, we = meta["t_window_start_us"], meta["t_window_end_us"]
        data = load_ulog(os.path.join(rdir, meta.get("ulog", "flight.ulg")))
        nav_t, nav = data["vehicle_status"]["timestamp"].astype(float), data["vehicle_status"]["nav_state"]
        print(f"nav_state values in {rdir}: {sorted(set(int(x) for x in nav))}", file=sys.stderr)
        for label, topic in (("truth", "vehicle_local_position_groundtruth"), ("estimate", "vehicle_local_position")):
            d = data[topic]
            t = d["timestamp"].astype(float)
            xyz = np.column_stack([d["x"], d["y"], d["z"]]).astype(float)
            ref = ref_ned(tr, hold, t0, t)
            nav_at = nav[np.clip(np.searchsorted(nav_t, t, side="right") - 1, 0, len(nav) - 1)]
            in_win = (t >= ws) & (t <= we)
            for scoring, mask in (("window&nav14", in_win & (nav_at == OFFBOARD)), ("window only", in_win)):
                m = score(ref, xyz, mask)
                if m["n"] == 0:
                    print(f"| {rdir} | {label} | {scoring} | 0 | n/a | n/a | n/a | n/a | n/a | n/a |")
                    continue
                print(f"| {rdir} | {label} | {scoring} | {m['n']} | {m['rms3d']:.3f} | {m['max3d']:.3f} | "
                      f"{m['rmsN']:.3f} | {m['rmsE']:.3f} | {m['rmsD']:.3f} | {m['err_first']:.3f} |")


if __name__ == "__main__":
    main()
