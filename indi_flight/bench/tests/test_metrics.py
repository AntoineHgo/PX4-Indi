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
    clean = out["effort"]["motor_rate_rms_per_s"]
    assert 3.2 < clean < 3.9, clean
    # force the publish stamp (what the old code did): zero-dt pairs are dropped, the remaining pairs span 2 ticks -> different
    am_bad = {k: v for k, v in am.items() if k != "timestamp_sample"}
    bad = M.compute(_fake_ulog({"actuator_motors": am_bad, "vehicle_status": vs}), run)
    assert bad["stamps"]["actuator_motors"]["stamp"] == "timestamp" and bad["stamps"]["actuator_motors"]["zero_dt_pairs"] > 0
    assert abs(bad["effort"]["motor_rate_rms_per_s"] - clean) > 0.05 * clean, (bad["effort"], clean)
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
    print(f"ok sample stamp: motor_rate_rms {clean:.3f}/s with timestamp_sample, {bad['effort']['motor_rate_rms_per_s']:.3f}/s with publish stamp")


def main():
    for f in (test_window_anchor_from_ulog, test_trajectory_functions, test_exact_and_lag, test_zoh_defect_and_fix, test_compute_end_to_end,
              test_sample_stamp_over_publish_stamp):
        f()
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
