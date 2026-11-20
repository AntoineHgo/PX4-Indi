"""Self-test of g52_check on synthetic runs with known answers (S138). Runs under pytest or `python3 test_g52_check.py`."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import g52_check as g  # noqa: E402

DT = 0.01


def _run(mode, zov=0.0, zsettle=0.5, xov=0.0, xsettle=0.5, zd=1.8, xd=3.0, tau=0.2):
    """Piecewise truth: z step at 3 s (2 s hold), x step at 11 s (2.5 s hold). Response = ramp to d at the release edge, then a
    decaying overshoot zov * exp(...)-like bump and an exponential tail a 5 % offset tail ends at *settle* s after release."""
    t = np.arange(0, 22.0, DT)
    p = np.zeros((len(t), 3))
    p[:, 2] = -10.0

    def seg(t_on, hold, d, ov, settle, axis, sgn):
        t_rel = t_on + hold
        s = np.where(t < t_rel, d * np.clip((t - t_on) / hold, 0, 1) * (t >= t_on), d)
        dt = t - t_rel
        m = dt >= 0
        bump = ov * np.sin(np.pi * np.clip(dt / 1.0, 0, 1)) * (dt <= 1.0)          # overshoot ov peaks 0.5 s after release
        tail = 0.05 * d * (dt < settle) if settle > 1.0 else 0.0    # 5 % of d decaying linearly to 0 at *settle*
        s = s + np.where(m, bump + tail * (dt > 1.0), 0.0)
        p[:, axis] += sgn * (s - 0)
        return
    seg(3.0, 2.0, zd, zov, zsettle, 2, -1.0)
    zfinal = zd
    if mode == "posctl":
        seg(11.0, 2.5, xd, xov, xsettle, 0, +1.0)
    st_t = np.arange(0, 22.0, 0.02)
    x = np.zeros(len(st_t), int)
    z = np.full(len(st_t), 500)
    z[(st_t >= 3.0) & (st_t < 5.0)] = 610
    if mode == "posctl":
        x[(st_t >= 11.0) & (st_t < 13.5)] = 400
    nav = {"t": t, "v": np.full(len(t), g.NAV[mode])}
    return {"t": st_t, "x": x, "z": z}, {"t": t, "p": p}, nav


def test_edges():
    st, _, _ = _run("posctl")
    assert g.edges(st["t"], st["z"], 500) == (3.0, 5.0)
    assert g.edges(st["t"], st["x"], 0) == (11.0, 13.5)


def test_pass_known_values():
    st, pos, nav = _run("posctl", zov=0.2, xov=0.4, zsettle=2.0, xsettle=3.0)
    r = g.evaluate("posctl", st, pos, nav)
    z, x = r["steps"]["z"], r["steps"]["x"]
    assert abs(z["d_m"] - 1.8) < 0.02 and abs(x["d_m"] - 3.0) < 0.02, (z["d_m"], x["d_m"])
    assert abs(z["overshoot_m"] - 0.2) < 0.02 and abs(x["overshoot_m"] - 0.4) < 0.02, (z["overshoot_m"], x["overshoot_m"])
    assert abs(z["settle_s"] - 2.0) < 0.05 and abs(x["settle_s"] - 3.0) < 0.05, (z["settle_s"], x["settle_s"])
    assert r["valid"] and r["passed"] and not r["loc"]


def test_fail_overshoot_and_settle():
    st, pos, nav = _run("posctl", zov=0.2, xov=0.7, zsettle=2.0, xsettle=5.0)
    r = g.evaluate("posctl", st, pos, nav)
    assert r["steps"]["x"]["overshoot_m"] > 0.5 and not r["steps"]["x"]["pass_overshoot"]
    assert r["steps"]["x"]["settle_s"] > 4.0 and not r["steps"]["x"]["pass_settle"]
    assert r["steps"]["z"]["pass_"] and not r["passed"]


def test_altctl_z_only_and_invalid_small_step():
    st, pos, nav = _run("altctl", zov=0.1, zsettle=1.0)
    r = g.evaluate("altctl", st, pos, nav)
    assert list(r["steps"]) == ["z"] and r["passed"]
    st, pos, nav = _run("altctl", zd=0.8)
    r = g.evaluate("altctl", st, pos, nav)
    assert not r["valid"] and not r["passed"]


def test_wrong_nav_state_invalid():
    st, pos, nav = _run("posctl")
    nav["v"][:] = 1
    r = g.evaluate("posctl", st, pos, nav)
    assert not r["valid"]


if __name__ == "__main__":
    for n, f in sorted(globals().items()):
        if n.startswith("test_"):
            f()
            print("ok", n)
