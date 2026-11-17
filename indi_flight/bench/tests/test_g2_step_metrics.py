"""Known-answer tests for bench/g2_step_metrics.py (pytest, synthetic arrays, no ULog)."""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import g2_step_metrics as G  # noqa: E402

US = 1e6
T_ON = 3.0 * US      # setpoint step time
T_START = 1.0 * US


def sp_series(steps, amp, t_end=12.0, hz=250):
    """steps: list of (t_s, level multiple of amp)."""
    t = np.arange(0, t_end, 1 / hz) * US
    x = np.zeros_like(t)
    for ts, lv in steps:
        x[t >= ts * US] = lv * amp
    return t, x


def run(est_fn, amp=15.0, steps=((3.0, 1.0),), lim=450.0, truth_fn=None, t_end=12.0):
    t_sp, sp = sp_series(list(steps), amp, t_end)
    t_e = np.arange(0, t_end, 1 / 400) * US
    est = est_fn(t_e / US)
    tr = est if truth_fn is None else truth_fn(t_e / US, est)
    return G.step_metrics(t_sp, sp, t_e, est, t_e, tr, abs(amp), T_START, lim)


def second_order(amp, zeta, wn, t0=3.0):
    def f(t):
        out = np.zeros_like(t)
        m = t >= t0
        tt = t[m] - t0
        wd = wn * math.sqrt(1 - zeta ** 2)
        out[m] = amp * (1 - np.exp(-zeta * wn * tt) * (np.cos(wd * tt) + zeta / math.sqrt(1 - zeta ** 2) * np.sin(wd * tt)))
        return out
    return f


def first_order(amp, tau, t0=3.0):
    return lambda t: np.where(t >= t0, amp * (1 - np.exp(-(t - t0) / tau)), 0.0)


def test_second_order_overshoot_and_settle():
    z, wn = 0.5, 20.0
    r = run(second_order(15.0, z, wn))
    assert abs(r["est_os_pct"] - 100 * math.exp(-math.pi * z / math.sqrt(1 - z ** 2))) < 0.15  # 16.3 %
    # brute force reference settle on a dense grid
    tt = np.arange(0, 3, 1e-5)
    wd = wn * math.sqrt(1 - z * z)
    y = 1 - np.exp(-z * wn * tt) * (np.cos(wd * tt) + z / math.sqrt(1 - z * z) * np.sin(wd * tt))
    ref = tt[np.nonzero(np.abs(y - 1) > 0.02)[0][-1]] * 1e3
    assert abs(r["est_settle_ms"] - ref) < 6.0  # one 400 Hz sample = 2.5 ms, plus first-in-band convention
    assert not r["pass"]  # OS 16 % > 5 %
    assert abs(r["t_on_us"] - T_ON) < 1


def test_first_order_no_overshoot():
    tau = 0.1
    r = run(first_order(15.0, tau))
    assert r["est_os_pct"] == 0.0 and r["truth_os_pct"] == 0.0
    assert abs(r["est_settle_ms"] - tau * math.log(50) * 1e3) < 4.0   # 391 ms
    assert abs(r["est_rise_ms"] - tau * math.log(9) * 1e3) < 3.0      # 220 ms
    assert r["pass"]


def test_negative_step_same_as_positive():
    a = run(second_order(15.0, 0.7, 25.0))
    b = run(second_order(-15.0, 0.7, 25.0), amp=-15.0)
    assert b["step_deg"] == -15.0
    for k in ("est_os_pct", "est_settle_ms", "est_rise_ms", "truth_os_pct"):
        assert abs(a[k] - b[k]) < 1e-9, k


def test_return_step_inside_window_is_excluded():
    # 3.0 s hold then return; est tracks the step with 0 % OS, but a 30 % glitch sits 40 ms before the return step
    steps = ((3.0, 1.0), (6.0, 0.0))
    base = first_order(15.0, 0.05)

    def est(t):
        y = base(t)
        y = np.where(t >= 6.0, 15.0 * np.exp(-(t - 6.0) / 0.05), y)  # follows the return
        g = (t >= 5.96) & (t < 6.0)
        return np.where(g, 15.0 * 1.3, y)
    r = run(est, steps=steps)
    assert abs(r["t_next_us"] - 6.0 * US) < 1
    assert abs(r["window_ms"] - 2950.0) < 1e-6
    assert r["est_os_pct"] == 0.0 and r["truth_os_pct"] == 0.0
    assert r["pass"]


def test_est_minus_truth_ramp():
    ramp = lambda t: 0.1 * (t - 3.0)   # deg, est - truth = +0.1 deg/s * (t-3), zero before
    r = run(first_order(15.0, 0.05), truth_fn=lambda t, est: est - np.where(t >= 3.0, ramp(t), 0.0),
            steps=((3.0, 1.0), (6.0, 0.0)))
    assert abs(r["est_minus_truth_pre_deg"]) < 1e-9
    # window [3, 5.95): last 1.5 s = [4.45, 5.95) -> mean of 0.1*(t-3) = 0.1*(5.2-3) = 0.22 deg
    assert abs(r["est_minus_truth_end_deg"] - 0.22) < 0.002


def test_never_settles_is_nan():
    # settles at 5 % beyond the step (outside the 2 % band) -> NaN; last window sample is outside the band
    r = run(lambda t: np.where(t >= 3.0, 15.0 * 1.05 * (1 - np.exp(-(t - 3.0) / 0.05)), 0.0))
    assert math.isnan(r["est_settle_ms"]) and not r["pass"]
    # sustained ringing: settle is the first in-band sample after the LAST violation, not the first zero crossing
    r2 = run(lambda t: np.where(t >= 3.0, 15.0 * (1 + 0.05 * np.sin(2 * math.pi * 4 * (t - 3.0))), 0.0),
             steps=((3.0, 1.0), (6.0, 0.0)))
    assert math.isnan(r2["est_settle_ms"]) or r2["est_settle_ms"] > 2800.0  # violation persists to the window end


def test_yaw_wrap_and_axis_limit():
    # yaw step 45 deg across the +-180 wrap: est/truth unwrapped from different starting points
    amp = 45.0
    r = run(first_order(amp, 0.2), amp=amp, lim=1350.0)
    assert r["pass"] and abs(r["est_settle_ms"] - 0.2 * math.log(50) * 1e3) < 4.0
    assert abs(G.wrap180(np.array([190.0]))[0] + 170.0) < 1e-9
