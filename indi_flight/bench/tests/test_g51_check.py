"""Self-test of g51_check on synthetic runs with known answers (S136). Runs under pytest or `python3 test_g51_check.py`."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import g51_check as g  # noqa: E402
import stick_profile as sp  # noqa: E402

MAXR = {"MC_ACRO_R_MAX": 100.0, "MC_ACRO_P_MAX": 100.0, "MC_ACRO_Y_MAX": 100.0}


def _sticks(mode, t_start=3.0, dt=0.03):
    t = np.arange(0, t_start + sp.steps_duration() + 3.0, dt)
    x = np.zeros(len(t), int); y = x.copy(); r = x.copy()
    for i, tt in enumerate(t):
        if tt >= t_start:
            x[i], y[i], r[i] = sp.step_sticks(tt - t_start, mode)
    return {"t": t, "x": x, "y": y, "r": r}


def _rates(st, sgn, tau, gain=1.0, dt=0.004):
    """First-order response w' = (gain*cmd - w)/tau of each axis, cmd = sgn * stick/1000 * 100 deg/s."""
    t = np.arange(st["t"][0], st["t"][-1], dt)
    w = np.zeros((len(t), 3))
    for ix, f in enumerate(("y", "x", "r")):
        cmd = np.radians(sgn[ix] * g.held(st["t"], st[f], t) / 1000.0 * 100.0)
        for i in range(1, len(t)):
            w[i, ix] = w[i - 1, ix] + dt * (gain * cmd[i - 1] - w[i - 1, ix]) / tau
    return {"t": t, "w": w}


def _common(st, tilt_fn=lambda t: 0 * t):
    t = np.arange(0, st["t"][-1], 0.01)
    return ({"t": t, "tilt_deg": tilt_fn(t)}, {"t": t, "z": 10 + 0 * t}, {"t": t, "v": np.full(len(t), 10)})


def test_edges_from_applied_sticks():
    st = _sticks("acro")
    e = g.stick_edges(st["t"], st["y"])
    assert abs(e[0] - 3.0) < 0.04 and abs(e[1] - 3.5) < 0.04 and abs(e[2] - 4.0) < 0.04
    e = g.stick_edges(st["t"], st["r"])
    assert abs(e[0] - 10.0) < 0.04


def test_acro_first_order_known_rms():
    # first order, tau 0.02, gain 1: RMS over [e+0.1, ...] of the residual is tiny (exp(-5) = 0.7 % of the step, 100 deg/s)
    st = _sticks("acro")
    tr = _rates(st, (+1, -1, +1), 0.02)
    att, z, nav = _common(st)
    r = g.evaluate("acro", st, tr, att, z, nav, MAXR)
    assert r["valid"] and r["pass"]
    for n in ("roll", "pitch", "yaw"):
        assert r["axes"][n]["rms_deg_s"] < 1.5
        assert abs(r["axes"][n]["rise_s"][0] - 0.02 * np.log(10)) < 0.01   # 90 % rise = tau ln 10
    # tau 0.1: residual amplitudes 100, 200 (cmd flips from +100 to -100), 100 (back to 0 from -100), decaying exp(-s/0.1):
    # analytic RMS over the pooled samples of the three plateaus (0.4 s, 0.4 s, 0.9 s)
    tr = _rates(st, (+1, -1, +1), 0.1)
    r = g.evaluate("acro", st, tr, att, z, nav, MAXR)
    tau = 0.1
    def i2(a, b, amp):   # integral of (amp exp(-s/tau))^2 over [a, b]
        return amp ** 2 * tau / 2 * (np.exp(-2 * a / tau) - np.exp(-2 * b / tau))
    want = np.sqrt((i2(0.1, 0.5, 100) + i2(0.1, 0.5, 200) + i2(0.1, 1.0, 100)) / (0.4 + 0.4 + 0.9))
    assert abs(r["axes"]["roll"]["rms_deg_s"] - want) < 0.05 * want, (r["axes"]["roll"]["rms_deg_s"], want)
    assert not r["pass"] or want <= 10   # want is about 5 deg/s: still a pass, the limit is the gate


def test_acro_sign_and_failing_cases():
    st = _sticks("acro")
    att, z, nav = _common(st)
    # wrong pitch sign convention in the vehicle (follows +x) must fail the pitch axis
    tr = _rates(st, (+1, +1, +1), 0.02)
    r = g.evaluate("acro", st, tr, att, z, nav, MAXR)
    assert not r["pass"] and not r["axes"]["pitch"]["pass"] and r["axes"]["roll"]["pass"]
    # 70 % gain: residual 30 deg/s on plateaus (roll) -> fail
    tr = _rates(st, (+1, -1, +1), 0.02, gain=0.7)
    r = g.evaluate("acro", st, tr, att, z, nav, MAXR)
    assert not r["pass"] and 18 < r["axes"]["roll"]["rms_deg_s"] < 23   # sqrt(30^2 x 0.8 / 1.7) = 20.6
    # wrong mode -> invalid
    nav2 = dict(nav, v=np.full(len(nav["t"]), 15))
    r = g.evaluate("acro", st, _rates(st, (+1, -1, +1), 0.02), att, z, nav2, MAXR)
    assert not r["valid"] and not r["pass"]


def test_stabilized_tilt_window():
    st = _sticks("stabilized")
    tr = {"t": np.arange(0, st["t"][-1], 0.01), "w": np.zeros((len(np.arange(0, st["t"][-1], 0.01)), 3))}
    nav = _common(st)[2]; nav["v"][:] = 15
    z = _common(st)[1]
    e3 = g.stick_edges(st["t"], st["y"])[2]
    # tilt 2 deg in the window passes; 4 deg inside the window fails; 4 deg before release + 1 s is ignored
    ok = g.evaluate("stabilized", st, tr, {"t": tr["t"], "tilt_deg": np.where(tr["t"] < e3 + 1.0, 17.0, 2.0)}, z, nav, MAXR)
    assert ok["pass"], ok
    bad = g.evaluate("stabilized", st, tr, {"t": tr["t"], "tilt_deg": np.where((tr["t"] > e3 + 1.2) & (tr["t"] < e3 + 1.4), 4.0, 1.0)}, z, nav, MAXR)
    assert not bad["pass"] and not bad["axes"]["roll"]["pass"] and bad["axes"]["pitch"]["pass"]
    # yaw rate residual 12 deg/s after the yaw doublet fails
    ey = g.stick_edges(st["t"], st["r"])[2]
    tr2 = dict(tr, w=np.zeros_like(tr["w"]))
    tr2["w"][(tr["t"] > ey + 1.5) & (tr["t"] < ey + 1.6), 2] = np.radians(12)
    r = g.evaluate("stabilized", st, tr2, {"t": tr["t"], "tilt_deg": 0 * tr["t"] + 1}, z, nav, MAXR)
    assert not r["axes"]["yaw"]["pass"] and r["axes"]["roll"]["pass"]


def test_loc_fails():
    st = _sticks("stabilized")
    tr = {"t": np.arange(0, st["t"][-1], 0.01)}
    tr["w"] = np.zeros((len(tr["t"]), 3))
    att, z, nav = _common(st, lambda t: np.where(t > 5, 85.0, 0.0))
    nav["v"][:] = 15
    assert g.evaluate("stabilized", st, tr, att, z, nav, MAXR)["loc"]


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f()
            print("ok", k)
