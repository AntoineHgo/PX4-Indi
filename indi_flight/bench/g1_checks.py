#!/usr/bin/env python3
"""Gate G1 checks behind bench/gate_g1.sh (host python: numpy + pyulog, no scipy).

  g1_checks.py g1.1 RUN_DIR...        logged rate vs declared rate (G1.1)
  g1_checks.py g1.3 SET_DIR           second keys vs metrics.json on SET_DIR/<scenario>/r*/ (G1.3)
  g1_checks.py g1.6a SPREAD_JSON      mode-instant spread vs 2 IMU periods (G1.6a)
  g1_checks.py selftest               checks the pass rules on synthetic timestamps
Exit 0 = pass, 1 = fail.
"""
import glob
import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
# topic -> declared rate [Hz]; "controller" = run.json rate_hz. Fixed rates from design/logging_profile.md
# (metrics.py reads vehicle_local_position and sim_ground_truth: trajectory.estimate / .truth).
# Truth is published at every physics step (1.25 ms = 800 Hz, T38 pre-test S19), so it is required at the controller rate:
# rate and attitude tracking are scored against truth at controller rate (the 400/267 Hz runs are still met by 800 Hz truth).
DECLARED = {
    "sensor_gyro": "controller",
    "vehicle_angular_velocity": "controller",
    "actuator_motors": "controller",
    "vehicle_torque_setpoint": "controller",
    "esc_status": "controller",
    # EKF2 output 800/9 = 88.9 Hz: IMU_INTEG_RATE 250 -> vehicle_imu integrates round(4 ms / 1.25 ms) = 3 samples = 3.75 ms;
    # EKF2_PREDICT_US 10000 -> down-sampler needs round(10 ms / 3.75 ms) = 3 IMU messages = 11.25 ms (88.0 = floor with margin)
    "vehicle_local_position": 88.0,
    # one sim-only topic (queue 16, publisher gz_bridge pose callback) replaces the three stock *_groundtruth topics, which the
    # logger decimates (queue 1, overwrite): position, velocity, attitude and angular velocity of the simulator at every step
    "sim_ground_truth": "controller",
}
GAP_PERIODS = 3.0
STARTUP_S = 1.0
# G1.3 tolerance: 1 % relative or the absolute floor, whichever is larger (1 mm / 0.1 deg / 0.1 % FS)
ABS_M, ABS_DEG = 1e-3, 0.1


def rate_verdict(ts, declared_hz):
    """ts: sample times [s]. Returns (median_hz, max_gap_s, ok). Gap rule applies after the first STARTUP_S seconds."""
    ts = np.asarray(ts, float)
    dt = np.diff(ts)
    med = 1.0 / np.median(dt)
    late = ts[1:] > ts[0] + STARTUP_S
    gap = float(dt[late].max()) if late.any() else float("nan")
    ok = bool(med >= declared_hz and gap < GAP_PERIODS / declared_hz)
    return med, gap, ok


def g11(runs):
    from pyulog import ULog
    allok = True
    print("| run | topic | declared Hz | median Hz | max gap ms | gap limit ms | verdict |")
    print("|---|---|---|---|---|---|---|")
    for run in runs:
        meta = json.load(open(os.path.join(run, "run.json")))
        u = ULog(os.path.join(run, "flight.ulg"), message_name_filter_list=list(DECLARED))
        name = "/".join(os.path.normpath(run).split(os.sep)[-3:])
        for t, dec in DECLARED.items():
            hz = float(meta["rate_hz"]) if dec == "controller" else dec
            ds = [d for d in u.data_list if d.name == t and d.multi_id == 0]
            if not ds:
                print(f"| {name} | {t} | {hz:g} | MISSING | | | FAIL |")
                allok = False
                continue
            d = ds[0].data
            ts = d.get("timestamp_sample", d["timestamp"]) * 1e-6
            med, gap, ok = rate_verdict(ts, hz)
            allok &= ok
            print(f"| {name} | {t} | {hz:g} | {med:.1f} | {gap * 1e3:.1f} | {GAP_PERIODS / hz * 1e3:.1f} | {'pass' if ok else 'FAIL'} |")
    print("G1.1 verdict:", "PASS" if allok else "FAIL")
    return allok


def agree(a, b, floor):
    return abs(a - b) <= max(0.01 * max(abs(a), abs(b)), floor)


def first_offboard_us(ulog_path):
    """Independent window key: first armed (arming_state 2) sample with nav_state offboard (14 or 23), ULog time."""
    from pyulog import ULog
    u = ULog(ulog_path, message_name_filter_list=["vehicle_status"])
    d = min([x for x in u.data_list if x.name == "vehicle_status"], key=lambda x: x.multi_id).data
    o = np.argsort(d["timestamp"], kind="stable")
    ts, arm, nav = d["timestamp"][o], d["arming_state"][o], d["nav_state"][o]
    hits = np.flatnonzero((arm == 2) & np.isin(nav, [14, 23]))
    return int(ts[hits[0]])


def g13(set_dir):
    runs = sorted(glob.glob(os.path.join(set_dir, "*", "r[0-9]")))
    bad = 0
    n = 0
    print("| run | metric | primary | second key | tol | verdict |")
    print("|---|---|---|---|---|---|")
    for r in runs:
        name = "/".join(r.split(os.sep)[-2:])
        meta = json.load(open(os.path.join(r, "run.json")))
        met = json.load(open(os.path.join(r, "metrics.json")))
        # window start: ULog offboard anchor + 3 s (OFFBOARD_SETTLE_S), tolerance 1 ms (second_key_window.py TOL_MS)
        t2 = (first_offboard_us(os.path.join(r, "flight.ulg")) + 3_000_000) * 1e-6
        t1 = met["window"]["start_s"]
        ok = abs(t1 - t2) < 1e-3
        n += 1
        bad += not ok
        print(f"| {name} | window.start_s | {t1:.5f} | {t2:.5f} | 1 ms | {'agree' if ok else 'DISAGREE'} |")
        if meta.get("trajectory"):
            out = subprocess.run([sys.executable, os.path.join(HERE, "second_key_traj.py"), r],
                                 capture_output=True, text=True, check=True).stdout
            for line in out.splitlines():
                c = [x.strip() for x in line.strip("|").split("|")]
                if len(c) >= 10 and c[2] == "window only" and c[1] in ("truth", "estimate"):
                    p = met["trajectory"][c[1]]
                    for key, sk in (("rms_3d_m", 4), ("max_dev_3d_m", 5)):
                        a, b = p[key], float(c[sk])
                        ok = agree(a, b, ABS_M)
                        n += 1
                        bad += not ok
                        print(f"| {name} | trajectory.{c[1]}.{key} | {a:.4f} | {b:.4f} | 1 % / 1 mm | {'agree' if ok else 'DISAGREE'} |")
    print(f"G1.3 compared keys: {n}, disagreements: {bad}")
    print("Primary metrics with NO second key yet (G1.3 expected output):")
    for m in ["rate_tracking.{roll,pitch,yaw}_rms_rad_s", "attitude_tracking.{rotation_angle,roll,pitch,yaw}_rms_deg",
              "position.rms_*_m / max_dev_*_m (hover hold)", "steps.* (rise / settle / overshoot)",
              "effort.* (motor_rate_rms_per_s, ...; also rate dependent, A-11)", "disturbance.* (peaks, recovery time)",
              "motor_fault.*", "control_allocator_status metrics", "trajectory.*.rms_horizontal / rms_vertical / rate_hz",
              "trajectory.zoh_legacy"]:
        print("  -", m)
    print("Covered by a second key: window.start_s (second_key_window.py logic), trajectory rms_3d / max_dev_3d (second_key_traj.py)")
    print("G1.3 verdict (covered keys only):", "PASS" if bad == 0 else "FAIL")
    return bad == 0


def g16a(path):
    res = json.load(open(path))
    allok = True
    print("| scenario | runs | ulog_anchor spread ms | IMU Hz | 2 IMU periods ms | verdict |")
    print("|---|---|---|---|---|---|")
    imu = float(os.environ.get("G1_IMU_HZ", "800"))
    for sc, v in res.items():
        row = v["rows"].get("window.ulog_anchor_s")
        if row is None:
            print(f"| {sc} | {len(v['runs'])} | MISSING | | | FAIL |")
            allok = False
            continue
        sp, lim = row["spread"] * 1e3, 2e3 / imu
        ok = sp <= lim
        allok &= ok
        print(f"| {sc} | {len(v['runs'])} | {sp:.2f} | {imu:g} | {lim:.2f} | {'pass' if ok else 'FAIL'} |")
    print("G1.6(a) verdict:", "PASS" if allok else "FAIL")
    return allok


def selftest():
    t = np.arange(0, 5, 1 / 800.0)
    assert rate_verdict(t, 800.0 - 1e-6)[2]
    assert not rate_verdict(t[::2], 800.0)[2]  # half rate
    assert not rate_verdict(np.delete(t, np.arange(2000, 2010)), 800.0)[2]  # 12.5 ms hole after start-up
    assert rate_verdict(np.delete(t, np.arange(100, 110)), 800.0)[2]  # hole inside the first second is ignored
    assert agree(1.0, 1.009, ABS_M) and not agree(1.0, 1.02, ABS_M) and agree(0.0, 0.0009, ABS_M)
    print("g1_checks selftest ok")


if __name__ == "__main__":
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "selftest":
        selftest()
        sys.exit(0)
    ok = g11(args) if cmd == "g1.1" else {"g1.3": g13, "g1.6a": g16a}[cmd](args[0])
    sys.exit(0 if ok else 1)
