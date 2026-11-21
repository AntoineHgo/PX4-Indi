#!/usr/bin/env python3
"""Synthetic self-test of bench/g510_score_motors.py (key 1), one test per defect D1-D4 of KEY2_MOTORS_S181.md plus a crash run.
Run: python3 bench/tests/test_g510_score_motors.py   (env G510_SCORE_PATH selects another copy, used for the break check)."""
import importlib.util, os, sys
import numpy as np

path = os.environ.get("G510_SCORE_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "../g510_score_motors.py"))
spec = importlib.util.spec_from_file_location("g510_score_motors", path)
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)


def qtilt(deg):  # roll by deg
    a = np.radians(deg) / 2
    return np.column_stack([np.cos(a), np.sin(a), 0 * a, 0 * a])


def make(kind, tilt_fn, h_fn, t_end, sat_fn=lambda t: np.ones_like(t), exit_status="ok", events=None, qd_fn=None,
         params=None, t_center=None):
    tm = np.arange(0, t_end, 1 / 800.0)
    tg = np.arange(0, t_end, 1 / 500.0)
    M = np.tile(sat_fn(tm)[:, None] * 1.0, (1, 4))
    h = h_fn(tg)
    D = dict(kind=kind, params=params or {"MPC_TILTMAX_AIR": 45.0, "MPC_MAN_TILT_MAX": 35.0}, tm=tm, M=M, tg=tg,
             qg=qtilt(tilt_fn(tg)), tp=tg, z_up=h, pos_ned=np.column_stack([0 * tg, 0 * tg, -h]), hold=[0, 0, -10.0],
             exit_status=exit_status, stick=None, sp=None)
    D["events"] = events or ({"settle": (5.0, 3.0), "sat": (8.0, 5.0)} if kind == "sat" else
                             {"settle": (5.0, 3.0), "full": (8.0, 1.0), "rec": (9.0, 9.0)})
    if kind == "stab":
        tc = np.arange(0, t_end, 1 / 46.0)
        tcen = t_center if t_center is not None else 9.0
        busy = (tc >= 8.0) & (tc < tcen)
        D["stick"] = (tc, busy)
        ts = np.arange(0, t_end, 1 / 89.0)
        D["sp"] = (ts, qtilt(qd_fn(ts) if qd_fn else 0 * ts))
    return D


hover = lambda t: 10.0 + 0 * t


def test_d1_exit_status_not_loc():
    D = make("stab", lambda t: 0 * t + 20, lambda t: 10 + 0 * t, 25.0, exit_status="failed", qd_fn=lambda t: 0 * t + 20)
    r = S.score(D)
    assert not r["loc"] and r["passed"], r


def test_d2_stab_tilt_limit_man_tilt_plus5_no_alt_limit():
    # tilt 42 deg: above MPC_MAN_TILT_MAX+5 = 40 (fail) although below MPC_TILTMAX_AIR+5 = 50
    r = S.score(make("stab", lambda t: np.where((t > 8) & (t < 9), 42.0, 0.0), hover, 25.0))
    assert r["tilt_limit_deg"] == 40.0 and not r["tilt_ok"] and not r["passed"], r
    # 3 m altitude loss in the stabilized part is not a failure
    r = S.score(make("stab", lambda t: 0 * t + 20, lambda t: np.where(t > 8.5, 7.0, 10.0), 25.0, qd_fn=lambda t: 0 * t + 20))
    assert r["passed"] and r["alt_loss_m"] > 2.0, r


def test_d3_stab_recovery_is_attitude_error_to_setpoint():
    # truth stays tilted 30 deg after centre, but the stick-commanded attitude is also 30 deg: error 0 -> recovered
    r = S.score(make("stab", lambda t: np.where(t > 8, 30.0, 0.0), hover, 25.0, qd_fn=lambda t: np.where(t > 8, 30.0, 0.0)))
    assert r["recovery_ok"] and r["passed"], r
    # truth level (tilt <= 5) but commanded attitude 30 deg: error 30 -> not recovered
    r = S.score(make("stab", lambda t: 0 * t, hover, 25.0, qd_fn=lambda t: np.where(t > 8, 30.0, 0.0)))
    assert not r["recovery_ok"], r
    # error decays to 0 at 1.5 s after centre: too slow
    r = S.score(make("stab", lambda t: np.where(t < 10.5, 20.0, 0.0), hover, 25.0))
    assert not r["recovery_ok"], r


def test_d4_no_rec_event_scored_not_crash():
    ev = {"settle": (5.0, 3.0), "sat": (8.0, 5.0)}
    D = make("sat", lambda t: np.where(t > 9, 60.0, 0.0), lambda t: np.where(t > 9, np.maximum(0, 10 - 20 * (t - 9)), 10.0), 10.5, events=ev)
    r = S.score(D)
    assert r["loc"] and not r["passed"], r
    D = make("stab", lambda t: np.where(t > 9, 60.0, 0.0), lambda t: np.where(t > 9, np.maximum(0, 10 - 20 * (t - 9)), 10.0), 10.5,
             events={"settle": (5.0, 3.0), "full": (8.0, 1.0)})
    r = S.score(D)
    assert r["loc"] and not r["passed"], r


def test_sat_checks_and_motors():
    good = make("sat", lambda t: 0 * t + 10, lambda t: np.where((t > 9) & (t < 12), 9.0, 10.0), 20.0)
    r = S.score(good)
    assert r["passed"] and abs(r["s_all4_ge_0.99"] - 5.0) < 1e-2 and r["tilt_limit_deg"] == 50.0, r
    r = S.score(make("sat", lambda t: 0 * t + 10, lambda t: np.where((t > 9) & (t < 12), 7.0, 10.0), 20.0))
    assert not r["alt_ok"] and not r["passed"], r  # 3 m loss > 2.0
    r = S.score(make("sat", lambda t: 0 * t + 10, hover, 20.0, sat_fn=lambda t: 0.5 + 0 * t))
    assert not r["motors_ok"] and not r["passed"], r  # motors never saturated
    r = S.score(make("sat", lambda t: 0 * t + 55, hover, 20.0))
    assert not r["tilt_ok"], r
    r = S.score(make("sat", lambda t: 0 * t + 10, lambda t: np.where(t > 13, 11.0, 10.0), 20.0))
    assert not r["recovery_ok"], r  # offset 1 m from hold never returns within 0.3 m


def test_sat_loc_not_flagged_in_landing():
    D = make("sat", lambda t: 0 * t + 10, lambda t: np.where(t > 14, 0.0, 10.0), 20.0,
             events={"settle": (5.0, 3.0), "sat": (8.0, 5.0), "land": (14.0, 0.0)})
    assert not S.score(D)["loc"]


if __name__ == "__main__":
    n = 0
    for k, f in sorted(globals().items()):
        if k.startswith("test_"):
            f()
            n += 1
    print(f"ok {n} tests")
