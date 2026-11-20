"""Self-test of g57_check / g53_hold_check on synthetic runs with known answers (S139). pytest or `python3 test_g57_check.py`."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import g53_hold_check as h  # noqa: E402
import g57_check as g  # noqa: E402

DT = 0.01
T_E = [7.0 + 2.0 * i for i in range(10)]


def _run57(thr_jump_at=None, thr_jump=0.0, tilt_at=None, tilt_deg=0.0, speed=3.0, states=None, validity="all", slow_at=()):
    t = np.arange(0, 32.0, DT)
    p = np.zeros((len(t), 3))
    p[:, 0] = speed * t
    for i in slow_at:                          # stop (zero speed) for 0.3 s around edge i
        m = (t >= T_E[i] - 0.15) & (t < T_E[i] + 0.15)
        p[m, 0] = p[np.flatnonzero(m)[0], 0]
        p[t >= T_E[i] + 0.15, 0] -= speed * 0.3
    p[:, 2] = -10.0
    nav_v = np.full(len(t), 2)
    for e, s in zip(T_E, states or g.EXPECT):
        nav_v[t >= e] = s
    c = np.full(len(t), 0.5)
    if thr_jump_at is not None:
        c[t >= T_E[thr_jump_at]] += thr_jump
    q_sp = np.tile([1.0, 0, 0, 0], (len(t), 1))
    q = q_sp.copy()
    if tilt_at is not None:                     # truth tilted about x by tilt_deg from edge + 0.4 to edge + 0.9 s
        m = (t >= T_E[tilt_at] + 0.4) & (t < T_E[tilt_at] + 0.9)
        a = np.radians(tilt_deg) / 2
        q[m] = [np.cos(a), np.sin(a), 0, 0]
    win = {"t_p0": 3.0, "t_end": 27.0, "t_end_end": 30.0}
    return g.evaluate(win, {"t": t, "v": nav_v}, {"t": t, "p": p}, {"t": t, "q": q}, {"t": t, "c": c}, {"t": t, "q": q_sp}, 0.5, validity)


def test_clean_pass():
    r = _run57()
    assert r["valid"] and r["passed"] and r["n_edges"] == 10 and r["n_fast"] == 10, r["invalid_reason"]
    assert max(e["thrust_step_pct_hover"] for e in r["edges"]) < 1e-6


def test_thrust_step_fails():
    r = _run57(thr_jump_at=3, thr_jump=0.15)          # 30 % of hover at edge 4
    assert r["valid"] and not r["thrust_ok"] and not r["passed"]
    assert abs(r["edges"][3]["thrust_step_pct_hover"] - 30.0) < 1.0
    r = _run57(thr_jump_at=3, thr_jump=0.08)          # 16 % passes
    assert r["thrust_ok"]


def test_tilt_fails():
    r = _run57(tilt_at=5, tilt_deg=8.0)
    assert not r["tilt_ok"] and not r["passed"] and abs(r["edges"][5]["tilt_err_deg"] - 8.0) < 0.1
    assert _run57(tilt_at=5, tilt_deg=4.0)["tilt_ok"]


def test_invalid_slow_and_states():
    r = _run57(speed=1.0)
    assert not r["valid"] and not r["passed"]
    st = list(g.EXPECT)
    st[4] = 1
    assert not _run57(states=st)["valid"]


def test_validity_leaveP():
    # edges leaving P (from == 2) are indices 0, 2, 4, 6; the other six may be slow (H brakes)
    slow = (1, 3, 5, 7, 8, 9)
    r = _run57(slow_at=slow, validity="leaveP")
    assert r["valid"] and r["n_leaveP"] == 4 and r["n_leaveP_fast"] == 4, r["invalid_reason"]
    assert not _run57(slow_at=slow)["valid"]                     # default rule: only 4 fast
    r = _run57(slow_at=(0,), validity="leaveP")                  # a P-leaving edge slow -> invalid
    assert not r["valid"] and r["n_leaveP_fast"] == 3


def _hold(drift=0.0, nav_bad=False):
    t = np.arange(0, 40.0, 0.02)
    p = np.zeros((len(t), 3))
    p[:, 0] = np.where(t >= 10.0, drift, 0.0)           # constant offset from the wind start
    nav = {"t": np.array([0.0, 5.0]), "v": np.array([2, 4])}
    if nav_bad:
        nav = {"t": np.array([0.0, 5.0, 20.0]), "v": np.array([2, 4, 2])}
    return h.evaluate(10.0, nav, {"t": t, "p": p})


def test_hold():
    r = _hold(0.2)
    assert r["valid"] and r["passed"] and abs(r["hold_rms_m"] - 0.2) < 0.01
    r = _hold(0.4)
    assert r["valid"] and not r["passed"]
    assert not _hold(0.0, nav_bad=True)["valid"]


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f()
            print(n, "ok")
