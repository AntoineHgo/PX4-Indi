#!/usr/bin/env python3
"""Self-test for indi_flight/bench/metrics.py trajectory scoring (plain asserts, no pytest, no ULog needed).

  python3 indi_flight/bench/tests/test_metrics.py
"""
import math
import os
import sys
from types import SimpleNamespace

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import metrics as M  # noqa: E402

LEMN = dict(shape="lemniscate", ax=4.0, ay=2.0, w=5.0 / math.sqrt(32.0), laps=2, ramp_s=3.0)  # scenarios.py LEMNISCATE
CIRC = dict(shape="circle", r=4.0, z_amp=1.0, w=7.0 / 4.0, laps=3, ramp_s=3.0)  # scenarios.py CIRCLE_FAST
HOLD = np.array([1.0, -2.0, -5.0])
T0 = 50_000_000  # us
HZ = 100.0


def dur(traj):
    return 2 * math.pi * traj["laps"] / traj["w"] + traj["ramp_s"]


def truth_fn(traj, t_us, delay_s=0.0):
    """Vehicle position (N,3) at times t_us when it follows the analytic path delayed by delay_s."""
    return M.analytic_reference(traj, T0, HOLD, np.asarray(t_us, float) - delay_s * 1e6)


def sample_times(traj, extra=3.0):
    return T0 + np.arange(-2.0, dur(traj) + extra, 1.0 / HZ) * 1e6


def test_trajectory_functions():
    for traj in (LEMN, CIRC):
        T = dur(traj)
        assert M.traj_phase(traj, -1.0) == 0.0 and M.traj_phase(traj, 0.0) == 0.0
        assert abs(M.traj_phase(traj, T) - 2 * math.pi * traj["laps"]) < 1e-9, "phase must end at laps*2pi"
        assert abs(M.traj_phase(traj, T + 5) - 2 * math.pi * traj["laps"]) < 1e-9
        p0 = M.traj_pos(traj, M.traj_phase(traj, 0.0))
        pe = M.traj_pos(traj, M.traj_phase(traj, T))
        assert max(abs(x) for x in p0) < 1e-12 and max(abs(x) for x in pe) < 1e-9, "closed path starts/ends at hold"
        # phase rate is continuous and bounded by w
        ts = np.arange(0, T, 0.01)
        ph = np.array([M.traj_phase(traj, t) for t in ts])
        assert (np.diff(ph) >= -1e-12).all() and np.diff(ph).max() / 0.01 <= traj["w"] * 1.0001
        # analytic_reference == hold + traj_pva()[0]
        ref = M.analytic_reference(traj, T0, HOLD, [T0 + 7.3e6])[0]
        assert np.allclose(ref, HOLD + np.array(M.traj_pva(traj, 7.3)[0]))
    # lemniscate cruise speed at phi=0 is w*sqrt(ax^2+4 ay^2) = 5 m/s
    t_c = LEMN["ramp_s"] + 0.0  # phase there is not 0; check peak speed instead
    sp = max(np.linalg.norm(M.traj_pva(LEMN, t)[1]) for t in np.arange(0, dur(LEMN), 0.02))
    assert abs(sp - 5.0) < 0.05, sp
    print(f"ok trajectory functions (lemniscate peak speed {sp:.3f} m/s)")


def test_exact_and_lag():
    for traj in (LEMN, CIRC):
        t = sample_times(traj)
        s = M.trajectory_error_analytic(t, truth_fn(traj, t), traj, T0, HOLD)
        assert s["rms_3d_m"] < 1e-9, s
        for d in (0.05, 0.1, 0.2):
            s = M.trajectory_error_analytic(t, truth_fn(traj, t, d), traj, T0, HOLD)
            spd = np.array([np.linalg.norm(M.traj_pva(traj, (x - T0) * 1e-6)[1]) for x in t])
            expect = d * math.sqrt(np.mean(spd ** 2))  # first order: |e| = d * |v|
            assert abs(s["rms_3d_m"] - expect) / expect < 0.05, (traj["shape"], d, s["rms_3d_m"], expect)
            print(f"ok {traj['shape']:10s} lag {d*1e3:4.0f} ms: rms {s['rms_3d_m']:.4f} m, d*v_rms {expect:.4f} m")


def test_zoh_defect_and_fix():
    """5 Hz logged setpoint + ZOH: a 100 ms lagging vehicle scores BETTER than a perfect one. Analytic reference does not."""
    traj = LEMN
    t = sample_times(traj)
    t_sp = T0 + np.arange(-2.0, dur(traj) + 3.0, 0.2) * 1e6  # logger rate 5 Hz
    sp = M.analytic_reference(traj, T0, HOLD, t_sp)  # setpoint logged exactly, only sampled at 5 Hz
    perfect, lag = truth_fn(traj, t), truth_fn(traj, t, 0.1)
    z_perf = M.trajectory_error_zoh(t, perfect, t_sp, sp)["rms_3d_m"]
    z_lag = M.trajectory_error_zoh(t, lag, t_sp, sp)["rms_3d_m"]
    a_perf = M.trajectory_error_analytic(t, perfect, traj, T0, HOLD)["rms_3d_m"]
    a_lag = M.trajectory_error_analytic(t, lag, traj, T0, HOLD)["rms_3d_m"]
    assert z_perf > 0.25, z_perf  # perfect tracker penalised ~0.3 m by the held reference
    assert z_lag < z_perf, "defect demonstration: legacy ZOH should reward the lagging vehicle"
    assert a_perf < 1e-9 < a_lag, (a_perf, a_lag)
    print(f"ok defect: ZOH perfect {z_perf:.3f} m > ZOH 100ms-lag {z_lag:.3f} m ; analytic perfect {a_perf:.1e} < lag {a_lag:.3f} m")


def _fake_ulog(topics):
    return SimpleNamespace(data_list=[SimpleNamespace(name=n, multi_id=0, data=d) for n, d in topics.items()])


def test_compute_end_to_end():
    traj = LEMN
    t = sample_times(traj).astype(np.int64)
    est, tru = truth_fn(traj, t, 0.1), truth_fn(traj, t)
    t_sp = (T0 + np.arange(-2.0, dur(traj) + 3.0, 0.2) * 1e6).astype(np.int64)
    sp = M.analytic_reference(traj, T0, HOLD, t_sp)
    lp = {"timestamp": t, "x": est[:, 0], "y": est[:, 1], "z": est[:, 2]}
    gt = {"timestamp": t, "x": tru[:, 0], "y": tru[:, 1], "z": tru[:, 2]}
    tsp = {"timestamp": t_sp, **{f"position[{i}]": sp[:, i] for i in range(3)}}
    vs = {"timestamp": np.array([t[0] - 3_000_000, t[-1]]), "nav_state": np.array([14, 14])}  # anchor+3 s = t[0]
    run = {"scenario": "synthetic", "t_window_start_us": int(t[0]), "t_window_end_us": int(t[-1]),
           "hold_pos_ned": list(HOLD), "trajectory": {**traj, "t0_us": T0, "dur_s": dur(traj)}}
    out = M.compute(_fake_ulog({"vehicle_local_position": lp, "sim_ground_truth": gt,
                                "trajectory_setpoint": tsp, "vehicle_status": vs}), run)
    tr = out["trajectory"]
    assert tr["time_base"]["status"] == "ok" and out["truth_source"] == "sim_ground_truth"
    assert tr["truth"]["rms_3d_m"] < 1e-9 and abs(tr["truth"]["rate_hz"] - HZ) < 1e-6
    assert 0.22 < tr["estimate"]["rms_3d_m"] < 0.32  # 100 ms lag, ~0.27 m over this window
    assert tr["zoh_legacy"]["rms_3d_m"] < tr["estimate"]["rms_3d_m"] and abs(tr["zoh_legacy"]["setpoint_rate_hz"] - 5.0) < 1e-6
    assert "rms_3d_m" not in tr, "legacy top-level key must be gone"
    # no groundtruth topic: truth is None, warning present
    out2 = M.compute(_fake_ulog({"vehicle_local_position": lp, "trajectory_setpoint": tsp, "vehicle_status": vs}), run)
    assert out2["trajectory"]["truth"] is None and any("groundtruth" in w for w in out2["warnings"])
    # t0 outside the window: flagged
    bad = dict(run, trajectory={**run["trajectory"], "t0_us": T0 + 10**12})
    out3 = M.compute(_fake_ulog({"vehicle_local_position": lp, "vehicle_status": vs}), bad)
    assert out3["trajectory"]["time_base"]["status"].startswith("SUSPECT")
    print(f"ok compute(): truth {tr['truth']['rms_3d_m']:.1e}, estimate(100ms lag) {tr['estimate']['rms_3d_m']:.3f}, "
          f"zoh_legacy {tr['zoh_legacy']['rms_3d_m']:.3f} m")


def test_window_anchor_from_ulog():
    """Window start = ULog nav_state transition (armed) + 3.0 s, NOT run.json t_window_start_us (here 0.7 s later)."""
    t = np.arange(0, 20_000_000, 10_000, dtype=np.int64)
    lp = {"timestamp": t, "x": np.zeros(t.size), "y": np.zeros(t.size), "z": np.zeros(t.size)}
    tr_us = 5_300_000  # PX4 enters offboard here; an earlier non-armed nav_state 14 sample must be ignored
    vs = {"timestamp": np.array([0, 1_000_000, tr_us, 18_000_000]), "nav_state": np.array([14, 2, 14, 2]),
          "arming_state": np.array([1, 2, 2, 2])}
    run = {"scenario": "synthetic", "t_window_start_us": tr_us + 3_700_000, "t_window_end_us": 15_000_000}
    out = M.compute(_fake_ulog({"vehicle_local_position": lp, "vehicle_status": vs}), run)
    w = out["window"]
    assert abs(w["start_s"] - (tr_us * 1e-6 + 3.0)) < 1e-9, w
    assert abs(w["runjson_start_s"] - 9.0) < 1e-9 and w["start_source"] == "ulog_nav_state+3.0", w
    assert abs(w["end_s"] - 14.3) < 1e-9 and abs(w["duration_s"] - 6.0) < 1e-9, w  # end = start + run.json duration
    # no armed offboard sample: fall back to run.json start
    vs2 = {"timestamp": np.array([0, 1_000_000]), "nav_state": np.array([2, 2]), "arming_state": np.array([1, 2])}
    w2 = M.compute(_fake_ulog({"vehicle_local_position": lp, "vehicle_status": vs2}), run)["window"]
    assert w2["start_source"] == "runjson" and abs(w2["start_s"] - 9.0) < 1e-9, w2
    print(f"ok window anchor: start {w['start_s']:.3f} s = transition {tr_us*1e-6:.3f} + 3.0 (run.json {w['runjson_start_s']:.3f})")


def test_sample_stamp_over_publish_stamp():
    """timestamp has zero-dt pairs (publish jitter) and timestamp_sample is clean: metrics must use the clean one.
    Also: truth from sim_ground_truth when present, fallback to the stock topic, a non-monotonic stamp gets sorted."""
    n, dt = 4000, 1250  # 800 Hz
    ts = (10_000_000 + np.arange(n) * dt).astype(np.int64)
    tp = ts.copy()
    tp[1::4] = tp[0::4]  # every 4th sample shares the previous publish stamp: zero-dt pairs
    assert (np.diff(tp) == 0).sum() == n // 4
    u = np.column_stack([0.5 + 0.1 * np.sin(2 * np.pi * np.arange(n) / 100.0 + k) for k in range(4)])
    am = {"timestamp": tp, "timestamp_sample": ts, **{f"control[{k}]": u[:, k] for k in range(4)}}
    vs = {"timestamp": np.array([7_000_000, 20_000_000]), "nav_state": np.array([14, 14])}  # anchor + 3 s = 10 s
    run = {"scenario": "synthetic", "t_window_start_us": 13_000_000, "t_window_end_us": 14_000_000}
    out = M.compute(_fake_ulog({"actuator_motors": am, "vehicle_status": vs}), run)
    assert out["stamps"]["actuator_motors"] == {"stamp": "timestamp_sample", "sorted": False, "zero_dt_pairs": 0}, out["stamps"]
    # truth value: du/dt with the clean stamp is 1.25 ms steps: d(0.1 sin)/dt rms ~ 0.1 * 2pi*8 Hz / sqrt2 ~ 3.55 /s
    clean = out["effort"]["motor_rate_rms_per_s_raw"]  # the stamp choice is visible in the RAW first difference
    assert 3.2 < clean < 3.9, clean
    assert abs(out["effort"]["motor_rate_rms_per_s"] - 0.1 * 2 * math.pi * 8 / math.sqrt(2)) < 0.02 * 3.55, out["effort"]
    # force the publish stamp (what the old code did): zero-dt pairs are dropped, the remaining pairs span 2 ticks -> different
    am_bad = {k: v for k, v in am.items() if k != "timestamp_sample"}
    bad = M.compute(_fake_ulog({"actuator_motors": am_bad, "vehicle_status": vs}), run)
    assert bad["stamps"]["actuator_motors"]["stamp"] == "timestamp" and bad["stamps"]["actuator_motors"]["zero_dt_pairs"] > 0
    assert abs(bad["effort"]["motor_rate_rms_per_s_raw"] - clean) > 0.05 * clean, (bad["effort"], clean)
    # non-monotonic sample stamp: sorted, with the columns reordered consistently
    o = np.arange(n)
    o[10], o[11] = 11, 10
    shuf = {k: v[o] for k, v in am.items()}
    d = M.ctrl_topic(_fake_ulog({"actuator_motors": shuf}), "actuator_motors", notes := {})
    assert notes["actuator_motors"]["sorted"] and (np.diff(d["timestamp"]) > 0).all() and np.array_equal(d["control[0]"], u[:, 0])
    # truth source: sim_ground_truth wins, stock topic is the fallback, none -> (None, None)
    tr = {"timestamp": ts, "timestamp_sample": ts, "x": np.zeros(n), "y": np.zeros(n), "z": np.zeros(n)}
    assert M.truth_local_position(_fake_ulog({"sim_ground_truth": tr, "vehicle_local_position_groundtruth": tr}))[1] == "sim_ground_truth"
    assert M.truth_local_position(_fake_ulog({"vehicle_local_position_groundtruth": tr}))[1] == "vehicle_local_position_groundtruth"
    assert M.truth_local_position(_fake_ulog({}))[0] is None
    print(f"ok sample stamp: motor_rate_rms {clean:.3f}/s with timestamp_sample, {bad['effort']['motor_rate_rms_per_s_raw']:.3f}/s with publish stamp (raw key)")


def test_step_metrics_analytic():
    """step_metrics on closed-form responses. First order (tau 0.1 s): delay_10 = tau ln(1/0.9), rise_10_90 = tau ln 9,
    settle_5 = tau ln 20, no overshoot, final error = -exp(-dur/tau). Second order (zeta 0.5): overshoot exp(-pi z / sqrt(1-z^2))."""
    tau, t0, dur, val = 0.1, 1.0, 2.0, 10.0
    t = np.arange(0.0, 5.0, 0.001)
    for sgn in (1.0, -1.0):  # a negative step must give the same normalised numbers
        x = np.where(t < t0, 0.0, sgn * val * (1.0 - np.exp(-(t - t0) / tau)))
        r = M.step_metrics(t, x, t0, dur, sgn * val, 1.0)
        assert abs(r["amplitude"] - sgn * val) < 1e-9, r
        assert abs(r["delay_10pct_s"] - tau * math.log(1 / 0.9)) < 2e-4, r
        assert abs(r["rise_10_90_s"] - tau * math.log(9.0)) < 2e-4, r
        assert abs(r["settle_5pct_s"] - tau * math.log(20.0)) < 2e-3, r
        assert r["overshoot_pct"] == 0.0, r
        assert abs(r["final_error_pct"] + 100.0 * math.exp(-dur / tau)) < 1e-3, r
    z, wn = 0.5, 10.0
    wd, k = wn * math.sqrt(1 - z * z), z / math.sqrt(1 - z * z)
    ts = np.maximum(t - t0, 0.0)
    y = np.where(t < t0, 0.0, 1.0 - np.exp(-z * wn * ts) * (np.cos(wd * ts) + k * np.sin(wd * ts)))
    r = M.step_metrics(t, val * y, t0, dur, val, 1.0)
    expect = 100.0 * math.exp(-math.pi * z / math.sqrt(1 - z * z))  # 16.30 %
    assert abs(r["overshoot_pct"] - expect) < 0.1, (r["overshoot_pct"], expect)
    assert r["settle_5pct_s"] is not None and 0.3 < r["settle_5pct_s"] < 0.7, r
    # amplitude below the floor is skipped; a response that never reaches the band is "not settled"
    assert "note" in M.step_metrics(t, np.zeros_like(t), t0, dur, 0.5, 1.0)
    ramp = np.where(t < t0, 0.0, (t - t0) * 2.0)  # still rising at the end of the 2 s segment, value 10
    assert M.step_metrics(t, ramp, t0, dur, val, 1.0)["settle_5pct_s"] is None
    print(f"ok step_metrics: rise {tau*math.log(9):.4f} s, settle {tau*math.log(20):.4f} s, overshoot {expect:.2f} %")


def _tracking_run(topics, w0_us=10_000_000, dur_us=4_000_000):
    """compute() on synthetic topics with an offboard anchor so that the window is [w0, w0 + dur] (anchor + 3 s = w0)."""
    vs = {"timestamp": np.array([w0_us - 3_000_000, w0_us + 20_000_000]), "nav_state": np.array([14, 14])}
    run = {"scenario": "synthetic", "t_window_start_us": w0_us, "t_window_end_us": w0_us + dur_us}
    return M.compute(_fake_ulog({**topics, "vehicle_status": vs}), run)


def test_rate_tracking_analytic():
    """Roll: measured 0.3 const vs setpoint 0.1 const -> rms 0.2. Pitch: measured 0.5 sin(2 pi 2 t), setpoint 0 ->
    0.5/sqrt2 (8 whole cycles in the 4 s window). Yaw: measured 0, setpoint -0.05 -> 0.05. Setpoint at 100 Hz, ZOH."""
    ta = np.arange(9_000_000, 16_000_000, 1000, dtype=np.int64)  # 1 kHz
    ts = np.arange(9_000_000, 16_000_000, 10_000, dtype=np.int64)  # 100 Hz
    sec = ta * 1e-6
    av = {"timestamp": ta, "timestamp_sample": ta, "xyz[0]": np.full(ta.size, 0.3),
          "xyz[1]": 0.5 * np.sin(2 * np.pi * 2.0 * sec), "xyz[2]": np.zeros(ta.size)}
    rsp = {"timestamp": ts, "roll": np.full(ts.size, 0.1), "pitch": np.zeros(ts.size), "yaw": np.full(ts.size, -0.05)}
    rt = _tracking_run({"vehicle_angular_velocity": av, "vehicle_rates_setpoint": rsp})["rate_tracking_estimate"]
    assert abs(rt["roll_rms_rad_s"] - 0.2) < 1e-9, rt
    assert abs(rt["pitch_rms_rad_s"] - 0.5 / math.sqrt(2.0)) < 2e-3, rt
    assert abs(rt["yaw_rms_rad_s"] - 0.05) < 1e-9, rt
    # ZOH, not interpolation: a setpoint that steps 0 -> 1 at 11 s against a constant 0 measurement; error is 1 for t >= 11 s
    # (window 10..14 s, so 3 s of 4 s): rms = sqrt(3/4)
    rsp2 = {"timestamp": ts, "roll": (ts >= 11_000_000).astype(float), "pitch": np.zeros(ts.size), "yaw": np.zeros(ts.size)}
    av2 = dict(av, **{"xyz[0]": np.zeros(ta.size), "xyz[1]": np.zeros(ta.size)})
    rt2 = _tracking_run({"vehicle_angular_velocity": av2, "vehicle_rates_setpoint": rsp2})["rate_tracking_estimate"]
    assert abs(rt2["roll_rms_rad_s"] - math.sqrt(0.75)) < 5e-3, rt2
    print(f"ok rate tracking: roll {rt['roll_rms_rad_s']:.4f} (0.2), pitch {rt['pitch_rms_rad_s']:.4f} ({0.5/math.sqrt(2):.4f}), "
          f"yaw {rt['yaw_rms_rad_s']:.4f} (0.05), step ZOH {rt2['roll_rms_rad_s']:.4f} ({math.sqrt(0.75):.4f})")


def test_attitude_tracking_analytic():
    """Constant 0.1 rad roll offset from the setpoint: rotation angle = roll rms = 5.7296 deg, pitch/yaw 0. Then a yaw error
    across the +-pi cut (measured pi-0.01, setpoint -pi+0.01): wrapped yaw error 0.02 rad, not 2 pi - 0.02; a sign-flipped
    setpoint quaternion (same rotation) must not change anything."""
    ta = np.arange(9_000_000, 16_000_000, 4000, dtype=np.int64)  # 250 Hz
    ts = np.arange(9_000_000, 16_000_000, 20_000, dtype=np.int64)  # 50 Hz

    def tile(q, n):
        return np.tile(np.asarray(q, float), (n, 1))

    def topics(q_att, q_sp):
        qa, qs = tile(q_att, ta.size), tile(q_sp, ts.size)
        return {"vehicle_attitude": {"timestamp": ta, "timestamp_sample": ta, **{f"q[{i}]": qa[:, i] for i in range(4)}},
                "vehicle_attitude_setpoint": {"timestamp": ts, **{f"q_d[{i}]": qs[:, i] for i in range(4)}}}
    th = 0.1
    at = _tracking_run(topics([math.cos(th / 2), math.sin(th / 2), 0, 0], [1, 0, 0, 0]))["attitude_tracking_estimate"]
    e = math.degrees(th)
    assert abs(at["rotation_angle_rms_deg"] - e) < 1e-6 and abs(at["roll_rms_deg"] - e) < 1e-6, at
    assert abs(at["pitch_rms_deg"]) < 1e-6 and abs(at["yaw_rms_deg"]) < 1e-6, at
    ya, yb = math.pi - 0.01, -math.pi + 0.01
    qa, qb = [math.cos(ya / 2), 0, 0, math.sin(ya / 2)], [math.cos(yb / 2), 0, 0, math.sin(yb / 2)]
    at2 = _tracking_run(topics(qa, qb))["attitude_tracking_estimate"]
    e2 = math.degrees(0.02)
    assert abs(at2["yaw_rms_deg"] - e2) < 1e-6 and abs(at2["rotation_angle_rms_deg"] - e2) < 1e-6, at2
    at3 = _tracking_run(topics(qa, [-v for v in qb]))["attitude_tracking_estimate"]
    assert abs(at3["rotation_angle_rms_deg"] - e2) < 1e-6 and abs(at3["yaw_rms_deg"] - e2) < 1e-6, at3
    print(f"ok attitude tracking: roll offset {at['roll_rms_deg']:.4f} deg ({e:.4f}), yaw wrap {at2['yaw_rms_deg']:.4f} deg ({e2:.4f})")


def _truth_topic(ta, q, w):
    """sim_ground_truth dict at times ta [us]; q (N,4) FRD->NED, w (N,3) FRD rates."""
    return {"timestamp": ta + 300, "timestamp_sample": ta, **{f"q[{i}]": q[:, i] for i in range(4)},
            **{f"angular_velocity[{i}]": w[:, i] for i in range(3)}}


def test_truth_rate_attitude_tracking():
    """Truth-based keys (rate_tracking, attitude_tracking) use sim_ground_truth only. Truth rates: roll 0.3 const, pitch
    0.5 sin(2 pi 2 t), yaw 0 against setpoint 0.1 / 0 / -0.05 -> 0.2, 0.5/sqrt2, 0.05. The ESTIMATE is made wildly different
    (offset 1.0 rad/s, 0.4 rad lag-like attitude error) and must change neither truth value, only the *_estimate keys and the
    estimator-error diagnostics (which are exactly the offsets). Truth attitude: 0.1 rad roll offset from q_d, truth stamped by
    timestamp_sample (publish stamp is 300 us later). No sim_ground_truth: truth keys None, estimate keys still filled."""
    ta = np.arange(9_000_000, 16_000_000, 1250, dtype=np.int64)  # 800 Hz
    ts = np.arange(9_000_000, 16_000_000, 10_000, dtype=np.int64)
    sec = ta * 1e-6
    w_tru = np.column_stack([np.full(ta.size, 0.3), 0.5 * np.sin(2 * np.pi * 2.0 * sec), np.zeros(ta.size)])
    th = 0.1
    q_tru = np.tile([math.cos(th / 2), math.sin(th / 2), 0, 0], (ta.size, 1))
    off = 0.4  # estimate roll error
    q_est = np.tile([math.cos((th + off) / 2), math.sin((th + off) / 2), 0, 0], (ta.size, 1))
    av = {"timestamp": ta, "timestamp_sample": ta, **{f"xyz[{i}]": w_tru[:, i] + 1.0 for i in range(3)}}
    att = {"timestamp": ta, "timestamp_sample": ta, **{f"q[{i}]": q_est[:, i] for i in range(4)}}
    rsp = {"timestamp": ts, "roll": np.full(ts.size, 0.1), "pitch": np.zeros(ts.size), "yaw": np.full(ts.size, -0.05)}
    qd = np.tile([1.0, 0, 0, 0], (ts.size, 1))
    asp = {"timestamp": ts, **{f"q_d[{i}]": qd[:, i] for i in range(4)}}
    topics = {"vehicle_angular_velocity": av, "vehicle_attitude": att, "vehicle_rates_setpoint": rsp, "vehicle_attitude_setpoint": asp}
    out = _tracking_run({**topics, "sim_ground_truth": _truth_topic(ta, q_tru, w_tru)})
    rt, at = out["rate_tracking"], out["attitude_tracking"]
    assert rt["source"] == "sim_ground_truth" and at["source"] == "sim_ground_truth"
    assert abs(rt["roll_rms_rad_s"] - 0.2) < 1e-9 and abs(rt["yaw_rms_rad_s"] - 0.05) < 1e-9, rt
    assert abs(rt["pitch_rms_rad_s"] - 0.5 / math.sqrt(2.0)) < 2e-3, rt
    assert abs(at["rotation_angle_rms_deg"] - math.degrees(th)) < 1e-6 and abs(at["roll_rms_deg"] - math.degrees(th)) < 1e-6, at
    # estimate keys see the estimate: rate error roll 1.3, attitude error th + off
    re = out["rate_tracking_estimate"]
    assert abs(re["roll_rms_rad_s"] - abs(0.3 + 1.0 - 0.1)) < 1e-9, re
    assert abs(out["attitude_tracking_estimate"]["rotation_angle_rms_deg"] - math.degrees(th + off)) < 1e-6
    # diagnostics: truth - estimate = -1.0 rad/s per axis, attitude -off
    ee, ae = out["rate_estimator_error"], out["attitude_estimator_error"]
    assert all(abs(ee[ax + "_mean_rad_s"] + 1.0) < 1e-9 and abs(ee[ax + "_rms_rad_s"] - 1.0) < 1e-9 for ax in AXES_), ee
    assert abs(ae["rotation_angle_rms_deg"] - math.degrees(off)) < 1e-6 and abs(ae["roll_mean_deg"] + math.degrees(off)) < 1e-6, ae
    # truth value identical when the estimate is removed entirely
    out_ne = _tracking_run({"vehicle_rates_setpoint": rsp, "vehicle_attitude_setpoint": asp,
                            "sim_ground_truth": _truth_topic(ta, q_tru, w_tru)})
    assert out_ne["rate_tracking"] == rt and out_ne["attitude_tracking"] == at
    # truth lagged by 20 ms behind the setpoint (same stamps, exact ZOH): pitch rms = A sqrt(1 - cos(w lag))
    lag = 0.02
    w_lag = np.column_stack([np.full(ta.size, 0.3), 0.5 * np.sin(2 * np.pi * 2.0 * (sec - lag)), np.zeros(ta.size)])
    rsp_s = {"timestamp": ta, "roll": np.full(ta.size, 0.3), "pitch": 0.5 * np.sin(2 * np.pi * 2.0 * sec), "yaw": np.zeros(ta.size)}  # un-lagged sine at the truth stamps
    o3 = _tracking_run({"vehicle_rates_setpoint": rsp_s, "sim_ground_truth": _truth_topic(ta, q_tru, w_lag)})
    exp = 0.5 * math.sqrt(1 - math.cos(2 * math.pi * 2.0 * lag))  # rms of A (sin(x) - sin(x - d)) = A sqrt(1 - cos d)
    assert abs(o3["rate_tracking"]["pitch_rms_rad_s"] - exp) < 1e-3 * exp, (o3["rate_tracking"], exp)
    # no sim_ground_truth: truth keys None (not the estimate), estimate keys intact, warning raised
    o4 = _tracking_run(topics)
    assert o4["rate_tracking"]["roll_rms_rad_s"] is None and o4["attitude_tracking"]["rotation_angle_rms_deg"] is None, o4["rate_tracking"]
    assert o4["rate_tracking_estimate"]["roll_rms_rad_s"] is not None and "rate_estimator_error" not in o4
    assert any("sim_ground_truth" in w for w in o4["warnings"])
    print(f"ok truth tracking: rate {rt['roll_rms_rad_s']:.3f}/{rt['pitch_rms_rad_s']:.3f}/{rt['yaw_rms_rad_s']:.3f}, att {at['rotation_angle_rms_deg']:.4f} deg; "
          f"estimate-invariant; lag {o3['rate_tracking']['pitch_rms_rad_s']:.4f} (analytic {exp:.4f}); no-truth -> None")


AXES_ = ("roll", "pitch", "yaw")


def _effort_rms(u, t_us, w0=10_000_000, w1=14_000_000):
    """motor_rate_bandlimited on u (N,) (single motor repeated)."""
    return M.motor_rate_bandlimited(t_us, np.column_stack([u, u]), w0, w1)


def test_effort_bandwidth():
    """D-EFFORT-BW: A sin(2 pi 5 t) -> rms of derivative A 2 pi f / sqrt2 within 2 %, at log rates 400/800/1000 Hz; white
    noise above 100 Hz changes it < 5 %; a 150 Hz sine is attenuated > 15x (net |H|^2 = 1/(1+(f/50)^4) -> 82x); refusal below
    400 Hz and with gaps > 10 ms over 0.1 % of the window, with the reason reported."""
    A, f = 0.1, 5.0
    exp = A * 2 * math.pi * f / math.sqrt(2)
    rng = np.random.default_rng(7)
    vals = {}
    for hz in (400, 800, 1000):
        t = (9_000_000 + np.arange(int(8.0 * hz)) * (1e6 / hz)).astype(np.int64)  # 9 s .. 17 s
        sec = t * 1e-6
        r = _effort_rms(0.5 + A * np.sin(2 * np.pi * f * sec), t)
        assert r["status"] == "ok" and abs(r["rms_per_s"] - exp) < 0.02 * exp, (hz, r, exp)
        vals[hz] = r["rms_per_s"]
        # white noise above 100 Hz (FFT-shaped: only bins >= 100 Hz), std 0.01 = 10 % of A
        nz = rng.standard_normal(t.size)
        F = np.fft.rfft(nz)
        F[np.fft.rfftfreq(t.size, 1.0 / hz) < 100.0] = 0
        nz = np.fft.irfft(F, t.size)
        nz *= 0.01 / nz.std()
        rn = _effort_rms(0.5 + A * np.sin(2 * np.pi * f * sec) + nz, t)
        assert abs(rn["rms_per_s"] - r["rms_per_s"]) < 0.05 * r["rms_per_s"], (hz, rn, r)
        vals[(hz, "noise")] = rn["rms_per_s"]
        # 150 Hz sine, same amplitude: raw derivative rms would be A 2 pi 150 / sqrt2; the filtered one must be > 15x smaller
        r150 = _effort_rms(0.5 + A * np.sin(2 * np.pi * 150.0 * sec), t)
        raw150 = A * 2 * math.pi * 150.0 / math.sqrt(2)
        assert r150["rms_per_s"] < raw150 / 15.0, (hz, r150, raw150)
        vals[(hz, "150Hz_atten")] = raw150 / r150["rms_per_s"]
    assert max(vals[h] for h in (400, 800, 1000)) / min(vals[h] for h in (400, 800, 1000)) < 1.01, vals
    # refusals
    t200 = (9_000_000 + np.arange(1600) * 5000).astype(np.int64)  # 200 Hz
    r = _effort_rms(0.5 + A * np.sin(2 * np.pi * f * t200 * 1e-6), t200)
    assert r["rms_per_s"] is None and "200 Hz < 400 Hz" in r["status"], r
    t = (9_000_000 + np.arange(6400) * 1250).astype(np.int64)
    keep = ~((t >= 11_000_000) & (t < 11_020_000))  # one 20 ms hole = 0.5 % of the 4 s window
    r = _effort_rms(0.5 + A * np.sin(2 * np.pi * f * t * 1e-6), t)  # sanity: full data fine
    assert r["status"] == "ok"
    rg = _effort_rms((0.5 + A * np.sin(2 * np.pi * f * t * 1e-6))[keep], t[keep])
    assert rg["rms_per_s"] is None and "gaps" in rg["status"], rg
    keep2 = ~((t >= 11_000_000) & (t < 11_003_000))  # 3 ms hole: below the 10 ms gap threshold, accepted
    assert _effort_rms((0.5 + A * np.sin(2 * np.pi * f * t * 1e-6))[keep2], t[keep2])["status"] == "ok"
    # through compute(): new key is the band-limited one, raw key kept, raw depends on noise, new one does not
    vs = {"timestamp": np.array([6_000_000, 20_000_000]), "nav_state": np.array([14, 14])}
    run = {"scenario": "synthetic", "t_window_start_us": 9_000_000, "t_window_end_us": 13_000_000}
    am = {"timestamp": t, "timestamp_sample": t, **{f"control[{k}]": 0.5 + A * np.sin(2 * np.pi * f * t * 1e-6) for k in range(4)}}
    o = M.compute(_fake_ulog({"actuator_motors": am, "vehicle_status": vs}), run)["effort"]
    assert abs(o["motor_rate_rms_per_s"] - exp) < 0.02 * exp and abs(o["motor_rate_rms_per_s_raw"] - exp) < 0.02 * exp, o
    print(f"ok effort bandwidth: 5 Hz rms {vals[400]:.4f}/{vals[800]:.4f}/{vals[1000]:.4f} (analytic {exp:.4f}) at 400/800/1000 Hz; "
          f"noise delta {[round(vals[(h, 'noise')] / vals[h] - 1, 4) for h in (400, 800, 1000)]}; "
          f"150 Hz attenuation {[round(vals[(h, '150Hz_atten')], 1) for h in (400, 800, 1000)]}x; refusals reported")


def main():
    for f in (test_window_anchor_from_ulog, test_trajectory_functions, test_exact_and_lag, test_zoh_defect_and_fix, test_compute_end_to_end,
              test_sample_stamp_over_publish_stamp,
              test_step_metrics_analytic, test_rate_tracking_analytic, test_attitude_tracking_analytic,
              test_truth_rate_attitude_tracking, test_effort_bandwidth):
        f()
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
