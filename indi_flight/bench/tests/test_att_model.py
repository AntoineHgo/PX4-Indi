"""T194: attitude-loop (rate-setpoint break) linear model: identity, limit, ideal-rate-loop case."""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import margins_est as ME  # noqa: E402
import margins_models as M  # noqa: E402

W = 2 * np.pi * np.geomspace(0.05, 0.45 * 800, 400)


def test_identity_indi():
    for fs in (800.0, 400.0, 266.7):
        w = 2 * np.pi * np.geomspace(0.05, 0.45 * fs, 400)
        for kw in (dict(), dict(sp_lead=False), dict(att_lat=3, att_p=5.0)):
            p = dict(M.HEAD_FLIGHT, **kw)
            lhs = 1 + M.L_indi(w, fs, **p)
            rhs = (1 + M.L_indi(w, fs, **dict(p, att_p=0.0))) * (1 + M.L_att_indi(w, fs, **kw))
            assert np.max(np.abs(lhs - rhs) / np.abs(lhs)) < 1e-9


def test_identity_pid():
    # 1 + L_pid_with_att = (1 + L_pid)(1 + L_att): the PID law has no attitude term, so build it from the setpoint path.
    fs = 800.0
    p = dict(M.PID_DEF)
    zi = np.exp(-1j * W / fs)
    Ii = p["Ki"] / fs * zi / (1 - zi)
    Pn = M._pn(zi, fs, p)
    Lm = M.L_pid(W, fs) + M._att_path(zi, fs, 8.0, 1) * (p["Kp"] + Ii) * p["G1"] * Pn
    rhs = (1 + M.L_pid(W, fs)) * (1 + M.L_att_pid(W, fs))
    assert np.max(np.abs(1 + Lm - rhs) / np.abs(rhs)) < 1e-9


def test_limit_att_p_zero():
    assert np.max(np.abs(M.L_att_indi(W, 800.0, att_p=0.0))) == 0.0
    assert np.max(np.abs(M.L_att_pid(W, 800.0, att_p=0.0))) == 0.0
    small = np.max(np.abs(M.L_att_indi(W, 800.0, att_p=1e-6)))
    assert small < 1e-4 * np.max(np.abs(M.L_att_indi(W, 800.0)))


def test_dc_closed_rate_loop_is_unity():
    # Pn scaling check: at 0.01 Hz the closed rate loop from setpoint to rate is 1 (INDI and PID).
    w = np.array([2 * np.pi * 0.01])
    for fn, kw in ((M.L_att_indi, dict(att_p=1.0)), (M.L_att_pid, dict(att_p=1.0))):
        zi = np.exp(-1j * w / 800.0)
        tcl = fn(w, 800.0, **kw) / M._att_path(zi, 800.0, 1.0, 1)
        assert abs(abs(tcl[0]) - 1.0) < 0.02, (fn.__name__, tcl)


def test_ideal_rate_loop_integrator_margins():
    # T_cl = 1, att_lat = 0: L = att_p T/(z-1); |L| = 1 at w = (2/T) asin(att_p T/2), PM = 90 deg - wT/2, no -180 crossing.
    for fs in (800.0, 400.0):
        T, ap = 1.0 / fs, 8.0
        w = 2 * np.pi * np.geomspace(0.05, 0.45 * fs, 400)
        zi = np.exp(-1j * w / fs)
        L = M._att_path(zi, fs, ap, 0)
        wc = 2 / T * math.asin(ap * T / 2)
        m = ME.margins(w, L)
        assert abs(m["pm_deg"] - (90 - math.degrees(wc * T / 2))) < 0.05
        assert abs(m["crossings"][0]["f_c"] - wc / 2 / math.pi) < 1e-3
        assert m["gm_db"] is None or (isinstance(m["gm_db"], float) and math.isnan(m["gm_db"])) or m["gm_db"] > 40


if __name__ == "__main__":
    for k, v in list(globals().items()):
        if k.startswith("test_"):
            v()
            print("PASS", k)
