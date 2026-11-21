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
    # S175: z band = max(2 % d, 0.10 m) = 0.10 m: the 5 % (0.09 m) tail is inside it, only the 0.2 m bump (exits 0.10 m at 0.83 s) counts;
    # the old 2 % band (settle_s_2pct) still gives 2.0 s. x keeps 2 % (3.0 s).
    assert abs(z["settle_s"] - 0.83) < 0.05 and abs(z["settle_s_2pct"] - 2.0) < 0.05 and abs(x["settle_s"] - 3.0) < 0.05, (z["settle_s"], z["settle_s_2pct"], x["settle_s"])
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


def test_z_band_floor_s175():
    """z d = 1.8 m: 2 % = 0.036 m, floor band 0.10 m. A 0.07 m tail lasting 3 s after release is inside the new band (settle ~ 0)
    and outside the old one (settle ~ 3 s); x keeps 2 % (a 0.07 m x tail of d = 3 m is outside its 0.06 m band)."""
    st, pos, nav = _run("posctl")
    t, p = pos["t"], pos["p"]
    m = (t >= 5.0) & (t < 8.0)
    p[m, 2] -= 0.07                                  # z up by 0.07 m after the z release (5 s) for 3 s
    r = g.evaluate("posctl", st, pos, nav)
    z = r["steps"]["z"]
    assert abs(z["settle_band_m"] - 0.10) < 1e-9
    assert z["settle_s"] < 0.1 and abs(z["settle_s_2pct"] - 3.0) < 0.05, (z["settle_s"], z["settle_s_2pct"])
    st, pos, nav = _run("posctl")
    t, p = pos["t"], pos["p"]
    m = (t >= 13.5) & (t < 16.5)
    p[m, 0] += 0.07
    x = g.evaluate("posctl", st, pos, nav)["steps"]["x"]
    assert abs(x["settle_band_m"] - 0.06) < 1e-9 and abs(x["settle_s"] - 3.0) < 0.05, x["settle_s"]
    # large step: 2 % of d above the floor (d = 8 m -> 0.16 m)
    st, pos, nav = _run("altctl", zd=8.0)
    assert abs(g.evaluate("altctl", st, pos, nav)["steps"]["z"]["settle_band_m"] - 0.16) < 1e-9


if __name__ == "__main__":
    for n, f in sorted(globals().items()):
        if n.startswith("test_"):
            f()
            print("ok", n)
