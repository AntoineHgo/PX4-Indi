"""Known-answer self-test for bench/g51_g52_key2.py core functions (synthetic data).
Run: python3 -m pytest bench/tests/test_g51_g52_key2.py   or   python3 bench/tests/test_g51_g52_key2.py"""
import os, sys, math
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import g51_g52_key2 as K

DT = 1.0 / 800


def acro_rms(tau):
    """first-order rate response to a 100 deg/s step at t=1; plateau [1.1, 1.5]."""
    t = np.arange(0, 3, DT)
    w = np.where(t >= 1, 100 * (1 - np.exp(-(t - 1) / tau)), 0.0)
    cmd = np.where(t >= 1, 100.0, 0.0)
    return K.plateau_rms(t, cmd - w, [(1.1, 1.5)])


def acro_expected(tau):
    # RMS of 100 exp(-s/tau) over s in [0.1, 0.5]
    return 100 * math.sqrt(tau / (2 * 0.4) * (math.exp(-0.2 / tau) - math.exp(-1.0 / tau)))


def test_acro_pass():
    tau = 0.05
    r = acro_rms(tau)
    assert abs(r - acro_expected(tau)) < 0.05 and r <= K.LIM['acro_rms']   # 3.38


def test_acro_fail():
    tau = 0.2
    r = acro_rms(tau)
    assert abs(r - acro_expected(tau)) < 0.2 and r > K.LIM['acro_rms']     # 30.0


def first_order_step(tau, d=2.0, t_rel=2.0):
    t = np.arange(0, 12, DT)
    s = np.where(t >= t_rel, d * (1 - np.exp(-(t - t_rel) / tau)), d * np.clip(t / t_rel, 0, 1))
    return t, s, d, t_rel


def test_settle_pass_and_fail():
    # release at 2.0 with the response still rising: s = d(1-exp(-(t-2)/tau)) is a
    # first-order approach to d from below. Last exit of 2 % band at tau ln(50) = 3.912 tau.
    t, s, d, tr = first_order_step(0.5)
    # here the approach starts at release; the series before release is irrelevant.
    os_, st = K.step_metrics(t, d * (1 - np.exp(-(t - tr) / 0.5)), tr, d)
    assert abs(st - 0.5 * math.log(50)) < 0.01 and os_ < 1e-9 and st <= K.LIM['settle']   # 1.956 PASS
    os_, st = K.step_metrics(t, d * (1 - np.exp(-(t - tr) / 1.2)), tr, d)
    assert abs(st - 1.2 * math.log(50)) < 0.01 and st > K.LIM['settle']                     # 4.694 FAIL


def test_overshoot_known():
    # after release: triangle up to d+ov at 0.5 s, then exponential decay tau 0.8
    d, ov, tau, tr = 2.0, 0.4, 0.8, 2.0
    t = np.arange(0, 12, DT)
    u = t - tr
    s = np.where(u < 0, d * t / tr, np.where(u < 0.5, d + ov * u / 0.5, d + ov * np.exp(-(u - 0.5) / tau)))
    os_, st = K.step_metrics(t, s, tr, d)
    assert abs(os_ - ov) < 1e-3 and os_ > K.LIM['z_os']                      # FAIL case (limit 0.3)
    assert abs(st - (0.5 + tau * math.log(ov / (0.02 * d)))) < 0.01          # 0.5+0.8 ln10 = 2.342


def test_loc():
    t = np.arange(0, 5, DT); h = np.full_like(t, 5.0); xy = np.zeros((len(t), 2)); ti = np.zeros_like(t)
    assert K.loc_check(t, ti, h, xy, 0, 5, tilt_hard=80) == []
    ti2 = ti.copy(); ti2[(t > 1) & (t < 1.1)] = 90.0
    assert any('tilt' in w for w in K.loc_check(t, ti2, h, xy, 0, 5, tilt_hard=80))
    assert any('ground' in w for w in K.loc_check(t, ti, np.where(t > 3, 0.1, 5.0), xy, 0, 5))


def test_segments():
    ts = np.arange(0, 6, 0.03)
    v = np.zeros_like(ts); v[(ts >= 1) & (ts < 1.5)] = 1000; v[(ts >= 1.5) & (ts < 2.0)] = -1000
    s = K.active_segments(ts, v, 0.0)
    assert len(s) == 2 and abs(s[0][0] - 1.02) < 0.04 and abs(s[1][1] - 2.01) < 0.04


if __name__ == '__main__':
    for n, f in list(globals().items()):
        if n.startswith('test_'):
            f(); print('ok', n)
