#!/usr/bin/env python3
"""Synthetic self-test of g58_moving_check_key2 with known answers. Run: python3 test_g58_moving_check_key2.py"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import g58_moving_check_key2 as k2  # noqa: E402

PARAMS = {'COM_RC_LOSS_T': 0.5, 'COM_DL_LOSS_T': 3, 'COM_OF_LOSS_T': 4.0, 'NAV_RCL_ACT': 1, 'NAV_DLL_ACT': 1,
          'COM_OBL_RC_ACT': 5}
DT = 0.01


def build(entry_delay=0.0, lag=0.5, frame_off=0.0, nan_s=0.0, gt_speed_nan=3.0, kind='rc', nav_new=4,
          v0=3.0, brake_t=3.0, params=None):
    """Offboard at v0 along +x; loss flag rises at 20.0; hold entered 20+entry_delay.
    After entry the setpoint brakes linearly from v0 to 0 over brake_t (position is the integral).
    Truth = setpoint position - lag (along x) + frame_off (along y), i.e. exactly known deviation.
    nan_s: first nan_s seconds of the window carry NaN position (velocity-only), truth moves at gt_speed_nan."""
    t = np.arange(0, 40, DT)
    te = 20.0 + entry_delay
    x0 = 0.0
    px = np.full_like(t, np.nan)
    py = np.zeros_like(t)
    vx = np.full_like(t, v0)
    pos = x0
    xs = np.zeros_like(t)
    for i in range(len(t)):
        if t[i] < te:
            vx[i] = v0
            pos += v0 * DT
        else:
            tau = t[i] - te
            vx[i] = max(v0 * (1 - tau / brake_t), 0.0)
            pos += vx[i] * DT
        xs[i] = pos
        px[i] = pos if t[i] >= te + nan_s else np.nan
    gx = xs - lag * (t >= te)  # truth = trajectory - lag once the failsafe window starts
    gy = np.full_like(t, frame_off)
    gvx = np.where(t < te, v0, vx)
    if nan_s > 0:
        m = (t >= te) & (t < te + nan_s)
        # truth moves at gt_speed_nan while the setpoint is velocity-only
        base = np.interp(te, t, xs)
        gx[m] = base + gt_speed_nan * (t[m] - te)
        # after the NaN segment truth snaps back onto the known position trajectory (lag as set)
    st = dict(t=np.array([0.0, 10.0, te]), nav=np.array([2, 14, nav_new]), armed=np.array([True] * 3))
    ft = np.arange(0, 40, 0.5)
    fl = dict(t=ft, rc=np.zeros(len(ft), int), dl=np.zeros(len(ft), int), ob=np.zeros(len(ft), int))
    fl[kind][ft >= 20.0] = 1
    return dict(status=st, flags=fl, sp=dict(t=t, px=px, py=py, vx=vx, vy=np.zeros_like(t)),
                gt=dict(t=t, x=gx, y=gy, vx=gvx, vy=np.zeros_like(t)), params=params or PARAMS)


def one(d):
    r = k2.analyze(d)
    assert len(r) == 1, r
    return r[0]


def close(a, b, tol, msg):
    assert abs(a - b) <= tol, '%s: %s vs %s' % (msg, a, b)


def main():
    # 1. truth lags a braking setpoint by exactly 0.5 m -> excursion 0.5, delay 0.01 grid, PASS
    r = one(build(entry_delay=0.0, lag=0.5))
    close(r['exc'], 0.5, 0.005, 'lag 0.5')
    close(r['delay'], 0.0, 0.011, 'delay')
    assert r['verdict'] == 'PASS' and r['nan_frac'] == 0.0 and r['entry_nav'] == 4, r
    close(r['speed'], 3.0, 1e-6, 'onset speed')
    # 2. lag 1.3 -> FAIL on excursion
    r = one(build(lag=1.3))
    close(r['exc'], 1.3, 0.005, 'lag 1.3')
    assert r['verdict'] == 'FAIL', r
    # 3. frame offset 0.8 m crosswise plus lag 0.6 along track -> hypot 1.0 exactly
    r = one(build(lag=0.6, frame_off=0.8))
    close(r['exc'], 1.0, 0.005, 'frame 0.8 + lag 0.6')
    r = one(build(lag=0.6, frame_off=0.9))
    close(r['exc'], math.hypot(0.6, 0.9), 0.005, 'frame 0.9 + lag 0.6')
    assert r['verdict'] == 'FAIL', r
    # frame helper: 1e-5 deg of latitude = 1.1119 m north, longitude scaled by cos(lat)
    n, e = k2._ll_offset(47.00001, 8.00001, 47.0, 8.0)
    close(n, 1.1119, 1e-3, 'lat')
    close(e, 1.1119 * math.cos(math.radians(47.0)), 1e-3, 'lon')
    # 4. delay 1.4 s after the flag -> FAIL on delay, excursion still computed
    r = one(build(entry_delay=1.4, lag=0.2))
    close(r['delay'], 1.4, 0.011, 'delay 1.4')
    assert r['verdict'] == 'FAIL' and 'delay' in r['why'], r
    r = one(build(entry_delay=0.9, lag=0.2))
    assert r['verdict'] == 'PASS', r
    # 5. NaN segment 1.0 s: velocity-only; truth at 2.5 m/s vs 3 m/s setpoint
    #    (braking setpoint vx=3-tau: deviation 0.5 tau - tau^2/2, peak 0.125 m at tau=0.5); fraction of window NaN = 1.0 / 15 (window = 15 s, no further nav change)
    r = one(build(nan_s=1.0, lag=0.0, gt_speed_nan=2.5))
    close(r['nan_frac'], 1.0 / 15.0, 0.002, 'nan fraction')
    close(r['exc'], 0.125, 0.01, 'integrated nan deviation')
    # valid-only excursion ignores the NaN segment (truth after it equals the trajectory: ~0)
    assert r['exc_valid'] is not None and r['exc_valid'] < 0.1, r
    # truth keeps 3 m/s while the velocity setpoint brakes (3-tau): deviation tau^2/2 = 0.5 m at tau=1
    r = one(build(nan_s=1.0, lag=0.0, gt_speed_nan=3.0))
    close(r['exc'], 0.5, 0.01, 'integrated nan deviation, truth not braking')
    # 6. wrong state entered (RTL configured, hold entered) -> FAIL; correct RTL -> PASS
    p = dict(PARAMS, NAV_RCL_ACT=2, COM_OBL_RC_ACT=5)
    r = one(build(kind='rc', nav_new=4, params=p))  # prior nav 14 -> COM_OBL_RC_ACT(5=hold) governs RC loss
    assert r['exp_nav'] == 4 and r['verdict'] == 'PASS', r
    p = dict(PARAMS, NAV_DLL_ACT=2)
    r = one(build(kind='dl', nav_new=4, params=p))
    assert r['exp_nav'] == 5 and r['verdict'] == 'FAIL', r
    r = one(build(kind='dl', nav_new=5, params=p))
    assert r['verdict'] == 'PASS', r
    r = one(build(kind='ob', nav_new=4, params=dict(PARAMS, COM_OBL_RC_ACT=4)))
    assert r['exp_nav'] == 18 and r['verdict'] == 'FAIL', r
    # 7. slow event is skipped, not passed as a moving event
    r = one(build(v0=0.5, brake_t=1.0))
    assert r['verdict'] == 'SKIP', r
    # 8. no nav change -> FAIL
    d = build()
    d['status'] = dict(t=np.array([0.0, 10.0]), nav=np.array([2, 14]), armed=np.array([True, True]))
    r = one(d)
    assert r['verdict'] == 'FAIL', r
    print('ALL PASS (%s)' % os.path.basename(__file__))


if __name__ == '__main__':
    main()
