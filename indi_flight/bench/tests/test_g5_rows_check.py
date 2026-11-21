"""Synthetic self-test for g5_rows_check (known answers). pytest or python3."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import g5_rows_check as g  # noqa: E402

S = 1_000_000


def vs_log(nav_changes=(), fs_rise=None, gcs_rise=None, end=120):
    t = np.arange(0, end * S, S // 10)
    nav = np.full(len(t), 4.0)
    for tc, v in nav_changes:
        nav[t >= tc] = v
    fs = np.zeros(len(t)); gl = np.zeros(len(t)); ar = np.full(len(t), 2.0)
    if fs_rise: fs[t >= fs_rise] = 1
    if gcs_rise: gl[t >= gcs_rise] = 1
    return {"timestamp": t, "nav_state": nav, "failsafe": fs, "gcs_connection_lost": gl, "arming_state": ar}


def pos_log(excursion=0.0, t_at=0, end=120):
    t = np.arange(0, end * S, 10_000)
    z = np.full(len(t), -3.0)
    z[t >= t_at] += excursion
    return {"timestamp": t, "x": np.zeros(len(t)), "y": np.zeros(len(t)), "z": z}


def l58(entry_off, exc):
    """offboard loss: last setpoint at 50 s, COM_OF_LOSS_T 4 s, nav 14 -> 4 at 54 + entry_off."""
    t_in = int((54 + entry_off) * S)
    L = {"vehicle_status": vs_log([(40 * S, 14), (t_in, 4)]), "gt": pos_log(exc, 52 * S),
         "offboard_control_mode": {"timestamp": np.arange(41 * S, 50 * S, S // 10)},
         "failsafe_flags": {"timestamp": np.array([0]), "manual_control_signal_lost": np.array([0])},
         "tel_gcs_ts": np.array([])}
    ev = [{"name": "offboard_mode", "t_applied_us": 41 * S}, {"name": "offboard_loss", "t_applied_us": 50 * S}]
    P = {"COM_OF_LOSS_T": 4.0, "COM_OBL_RC_ACT": 0}
    ch = [(0, "COM_OBL_RC_ACT", 5)]  # runtime param set must be respected
    return [r for r in g.g58(L, ev, P, ch) if "offboard" in r["name"]][0]


def test_g58_offboard():
    assert l58(0.3, 0.2)["status"] == "PASS"
    assert l58(1.5, 0.2)["status"] == "FAIL"   # entry 1.5 s after timeout
    assert l58(0.3, 1.5)["status"] == "FAIL"   # excursion 1.5 m


def test_g58_rc_failsafe_rise_and_link_gcs():
    ev = [{"name": "rc_loss", "t_applied_us": 20 * S}, {"name": "link_loss", "t_applied_us": 60 * S}]
    ff = {"timestamp": np.array([0, 20.6 * S, 21 * S]), "manual_control_signal_lost": np.array([0, 1, 1])}
    vs = vs_log(fs_rise=int(20.7 * S), gcs_rise=int(64.5 * S))
    L = {"vehicle_status": vs, "gt": pos_log(), "failsafe_flags": ff, "offboard_control_mode": {"timestamp": np.array([0])},
         "tel_gcs_ts": np.array([58 * S, 60.5 * S])}
    P = {"COM_RC_LOSS_T": 0.5, "NAV_RCL_ACT": 1, "COM_DL_LOSS_T": 3.0, "NAV_DLL_ACT": 1}
    r = {x["name"].split()[1]: x for x in g.g58(L, ev, P, [])}
    assert r["rc_loss"]["status"] == "PASS" and abs(r["rc_loss"]["entry_minus_timeout_s"] - 0.6) < 1e-6
    assert abs(r["link_loss"]["entry_minus_timeout_s"] - 1.0) < 1e-6   # 64.5 - (60.5 + 3)
    assert r["link_loss"]["status"] == "PASS"                         # exactly the 1 s limit passes
    P["COM_DL_LOSS_T"] = 2.0                                          # timeout earlier -> 2 s late -> FAIL
    assert g.g58(L, ev, P, [])[1]["status"] == "FAIL"


def motors_log(zero_after_ms, end_s=20, kill_s=10):
    t = np.arange(0, end_s * S, 1250)
    M = np.full((len(t), 4), 0.4)
    if zero_after_ms is not None:
        M[t >= kill_s * S + zero_after_ms * 1000] = 0.0
    d = {"timestamp": t}
    for i in range(4): d[f"control[{i}]"] = M[:, i]
    return d


def outputs_log(zero_after_ms, spacing_us=1250, end_s=20, kill_s=10):
    t = np.arange(0, end_s * S, spacing_us)
    O = np.full((len(t), 4), 1500.0)
    if zero_after_ms is not None:
        O[t >= kill_s * S + zero_after_ms * 1000] = 0.0
    d = {"timestamp": t}
    for i in range(4): d[f"output[{i}]"] = O[:, i]
    return d


def test_g59a():
    ev = [{"name": "kill", "t_applied_us": 10 * S}]
    sw = {"timestamp": np.array([0, 10 * S + 500]), "kill_switch": np.array([3, 1])}
    # (output zero after ms, output spacing us, expected verdict of "G5.9a kill motors")
    for zms, sp, st in ((0.0, 1250, "PASS"), (50.0, 1250, "FAIL"), (None, 1250, "FAIL"), (5.0, 10_000, "NOT-COMPUTED")):
        L = {"manual_control_switches": sw, "actuator_motors": motors_log(None), "vehicle_status": vs_log(end=20),
             "actuator_outputs": outputs_log(zms, sp),
             "actuator_armed": {"timestamp": np.array([0]), "kill": np.array([0])}}
        L["vehicle_status"]["arming_state"][:] = 2
        r = {x["name"]: x for x in g.g59a(L, ev, 1250)}
        assert r["G5.9a kill motors"]["status"] == st, (zms, sp, r["G5.9a kill motors"])
        assert r["G5.9a kill command (info)"]["status"] == "INFO"  # actuator_motors never decides the row


def test_g59a_kill_flag_reference_s175():
    """Reference is the actuator_armed.kill rise (10 s + 8.75 ms), not the switch change (10 s + 0.5 ms): outputs 0 at
    kill + 1.0 ms PASS (1.0 <= 1.25; relative to the switch it would be 9.25 ms), at kill + 3 ms FAIL; latency 8.25 ms reported."""
    ev = [{"name": "kill", "t_applied_us": 10 * S}]
    sw = {"timestamp": np.array([0, 10 * S + 500]), "kill_switch": np.array([3, 1])}
    aa = {"timestamp": np.array([0, 10 * S + 8750]), "kill": np.array([0, 1])}
    for after_kill_us, st in ((1000, "PASS"), (3000, "FAIL")):
        zero_ms = 8.75 + after_kill_us / 1000
        L = {"manual_control_switches": sw, "actuator_motors": motors_log(None), "vehicle_status": vs_log(end=20),
             "actuator_outputs": outputs_log(zero_ms, 250), "actuator_armed": aa}
        L["vehicle_status"]["arming_state"][:] = 2
        r = {x["name"]: x for x in g.g59a(L, ev, 1250)}
        assert r["G5.9a kill motors"]["status"] == st, (after_kill_us, r["G5.9a kill motors"])
        assert abs(r["G5.9a commander latency (info)"]["commander_latency_ms"] - 8.25) < 1e-6
        assert abs(r["G5.9a kill motors"]["delay_ms"] - after_kill_us / 1000) < 0.3


def indi_logs(t_arm, pos_nonzero, first_dt_ms=10):
    n = 100
    tp = t_arm + first_dt_ms * 1000 + np.arange(n) * 10_000
    pos = {"timestamp": tp}
    for k in g.POS_STATES: pos[k] = np.full(n, 1.0 if pos_nonzero else 0.0)
    for k in g.POS_MEAS: pos[k] = np.full(n, 9.74)  # filtered measurements track their input: non-zero at rest, not a state
    rate = {"timestamp": tp}
    for k in g.RATE_STATES: rate[k] = np.zeros(n)
    for k in g.RATE_MEAS: rate[k] = np.full(n, 0.3)
    return {"indi_pos_status": pos, "indi_rate_status": rate}


def test_g59b():
    ta = 100 * S
    assert g.g59b(indi_logs(ta, False), ta)["status"] == "PASS"
    assert g.g59b(indi_logs(ta, True), ta)["status"] == "FAIL"
    assert g.g59b(indi_logs(ta, False, 500), ta)["status"] == "NOT-COMPUTED"   # late first sample is not a zero


def test_g59c():
    ta = 100 * S
    t = np.arange(ta, ta + 3 * S, 1250)
    for jump, st in ((0.02, "PASS"), (0.08, "FAIL")):
        u = np.full(len(t), 0.05); u[t >= ta + 0.5 * S] += jump
        d = {"timestamp": t, **{f"control[{i}]": u for i in range(4)}}
        assert g.g59c({"actuator_motors": d}, ta)["status"] == st


def test_g59d():
    ta = 100 * S
    edge = 110 * S
    ts = {"timestamp": np.array([ta, edge - 1, edge]), "takeoff_state": np.array([3, 4, 5])}
    tp = np.arange(edge - 3 * S // 10, edge + 3 * S // 10, 10_000)
    for step, dip, st in ((0.005, 0.1, "PASS"), (0.05, 0.1, "FAIL"), (0.005, 0.5, "FAIL")):
        th = np.where(tp >= edge, 0.3 + step, 0.3)
        tg = np.arange(edge - S, edge + 2 * S, 10_000)
        z = np.where(tg >= edge + S // 2, -3.0 + dip, -3.0)  # NED z up means altitude loss
        L = {"takeoff_status": ts, "indi_pos_status": {"timestamp": tp, "thrust": th}, "gt": {"timestamp": tg, "z": z}}
        assert g.g59d(L, ta, 0.137)["status"] == st, (step, dip)
    L["indi_pos_status"] = {"timestamp": tp[tp < edge], "thrust": th[tp < edge]}
    assert g.g59d(L, ta, 0.137)["status"] == "NOT-COMPUTED"


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("ok", n)
