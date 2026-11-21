import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import g511_check as g

T = np.arange(0, 10, 0.01)


def zb_step(deg, ta=5.0):
    a = np.where(T >= ta, np.radians(deg), 0.0)  # tilt about x
    return np.stack([np.zeros_like(a), -np.sin(a), np.cos(a)], 1)


def test_tilt():
    assert g.tilt_jump_deg(T, zb_step(2.0), 5.0) > g.TILT_LIM_DEG
    assert g.verdict(True, g.tilt_jump_deg(T, zb_step(2.0), 5.0), 0.0, False) == "FAIL"
    j = g.tilt_jump_deg(T, zb_step(0.5), 5.0)
    assert abs(j - 0.5) < 1e-6 and g.verdict(True, j, 0.0, False) == "PASS"


def test_excursion():
    pos = np.zeros((len(T), 3)); pos[T >= 5.0, 0] = 0.6
    e = g.excursion_m(T, pos, 5.0)
    assert abs(e - 0.6) < 1e-9 and g.verdict(True, 0.0, e, False) == "FAIL"
    pos[T >= 5.0, 0] = 0.3
    assert g.verdict(True, 0.0, g.excursion_m(T, pos, 5.0), False) == "PASS"


def test_invalid_and_osc():
    assert g.verdict(False, 0, 0, False) == "INVALID"
    assert g.verdict(True, 0, 0, True) == "FAIL"
    cnt = np.where(T >= 5.0, 1, 0)
    ok, why, _ = g.validity(5.0, T, cnt, T, np.full(len(T), 4), [], "ekf_yaw")
    assert ok, why
    ok, why, _ = g.validity(5.0, T, cnt, T, np.where(T > 7, 14, 4), [], "ekf_yaw")
    assert not ok


def test_yaw():
    yaw = np.where(T >= 5.0, np.radians(5.0), 0.0)
    assert abs(g.yaw_change_deg(T, yaw, 5.0)[0] - 5.0) < 1e-6
    assert abs(g.sp_yaw_step_deg(T, yaw, 5.0) - 5.0) < 1e-6


def test_excursion_h_and_verdict_s175():
    pos = np.zeros((len(T), 3)); pos[T >= 5.0, 2] = 0.9; pos[T >= 5.0, 0] = 0.3      # z (vertical) 0.9 m, horizontal 0.3 m
    assert abs(g.excursion_h_m(T, pos, 5.0) - 0.3) < 1e-9 and g.excursion_m(T, pos, 5.0) > 0.9
    assert g.verdict_s175("ekf_xy", True, 9.0, 0.3, 0.95, False) == "PASS"          # tilt jump does not judge xy; vertical ignored
    assert g.verdict_s175("ekf_xy", True, 0.0, 0.6, 0.6, False) == "FAIL"
    assert g.verdict_s175("ekf_xy", True, 0.0, 0.1, 0.1, True) == "FAIL"             # oscillation
    assert g.verdict_s175("ekf_yaw", True, 0.9, 0.0, 0.1, False) == "PASS"
    assert g.verdict_s175("ekf_yaw", True, 1.1, 0.0, 0.1, False) == "FAIL"
    assert g.verdict_s175("ekf_yaw", False, 0.0, 0.0, 0.0, False) == "INVALID"


def test_noevent_p95_excess_s175():
    """Setpoint tilt: 0.8 deg step every 4 s in 0..40 s (no-event steps), event step of 1.5 deg at 50 s. No-event metric =
    0.8 deg everywhere a step lies in the window, 0 elsewhere -> p95 = 0.8; excess = 1.5 - 0.8 = 0.7 (PASS), a 2.0 deg event -> 1.2 (FAIL)."""
    t = np.arange(0, 60, 0.01)
    a = np.zeros_like(t)
    for k in range(4, 40, 4):
        a[t >= k] += np.radians(0.8) * (1 if (k // 4) % 2 else -1)
    a[t >= 50.0] += np.radians(1.5)
    zb = np.stack([np.zeros_like(a), -np.sin(a), np.cos(a)], 1)
    nav_t = np.arange(0, 60, 0.1)
    nav = np.full(len(nav_t), 4)
    tt, v = g.noevent_tilt_jumps(t, zb, nav_t, nav, 4, [50.0])
    assert len(v) > 20 and tt.max() < 50.0 - 2.0 + 1e-9                       # event window excluded
    p95 = g.noevent_p95(v)
    assert abs(p95 - 0.8) < 0.02, p95
    ev = g.tilt_jump_deg(t, zb, 50.0)
    assert abs((ev - p95) - 0.7) < 0.03 and g.verdict_s175("ekf_yaw", True, ev - p95, 0, 0, False) == "PASS"
    assert g.verdict_s175("ekf_yaw", True, 2.0 - p95, 0, 0, False) == "FAIL"
    nav2 = np.where(nav_t < 20, 14, 4)                                          # other nav_state before 20 s is skipped
    tt2, _ = g.noevent_tilt_jumps(t, zb, nav_t, nav2, 4, [50.0])
    assert tt2.min() >= 21.0 - 1e-9


def test_check_run_subtracts_p95(tmp_path=None):
    """End to end through check_run (load patched): no-event setpoint steps of 0.8 deg (p95 0.8), ekf_yaw event step 1.5 deg at 50 s.
    Reported jump 1.5 deg > 1 deg limit, but excess 0.7 deg -> PASS; without the p95 subtraction the verdict would be FAIL."""
    import json, tempfile
    d0 = tmp_path or tempfile.mkdtemp()
    t = np.arange(0, 60, 0.01)
    a = np.zeros_like(t)
    for k in range(4, 40, 4):
        a[t >= k] += np.radians(0.8) * (1 if (k // 4) % 2 else -1)
    a[t >= 50.0] += np.radians(1.5)
    qd = np.stack([np.cos(a / 2), np.sin(a / 2), 0 * a, 0 * a], 1)
    n = len(t)
    gt = {"timestamp": t * 1e6, "x": np.zeros(n), "y": np.zeros(n), "z": np.zeros(n)}
    for i in range(3):
        gt[f"angular_velocity[{i}]"] = np.zeros(n)
    for i, v in enumerate((1.0, 0, 0, 0)):
        gt[f"q[{i}]"] = np.full(n, v)
    sp = {"timestamp": t * 1e6}
    for i in range(4):
        sp[f"q_d[{i}]"] = qd[:, i]
    tv = np.arange(0, 60, 0.1)
    cnt = lambda k: {"timestamp": tv * 1e6, k: (tv >= 50.0).astype(int)}
    zero = {"timestamp": tv * 1e6, "xy_reset_counter": np.zeros(len(tv), int)}
    d = {"sim_ground_truth": gt, "vehicle_attitude_setpoint": sp, "vehicle_status": {"timestamp": tv * 1e6, "nav_state": np.full(len(tv), 4)},
         "vehicle_attitude": cnt("quat_reset_counter"), "vehicle_local_position": zero}
    json.dump({"g5_events": [dict(name="ekf_yaw", t_cmd_us=49.9e6, t_applied_us=50.0e6), dict(name="ekf_xy", t_cmd_us=1e9, t_applied_us=1e9)]},
              open(os.path.join(d0, "run.json"), "w"))
    old = g.load
    g.load = lambda run: d
    try:
        r = g.check_run(d0, d0)[0]
    finally:
        g.load = old
    assert r["event"] == "ekf_yaw" and r["valid"], r
    assert abs(r["tilt_jump_deg"] - 1.5) < 0.03 and abs(r["noevent_p95_deg"] - 0.8) < 0.02, r
    assert abs(r["tilt_excess_deg"] - 0.7) < 0.04 and r["verdict"] == "PASS", r
    assert r["legacy"] == "FAIL"                                              # raw jump alone fails: the subtraction decides


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("ok", n)
