#!/usr/bin/env python3
"""Self-test of bench/auto_smoke_check.py on synthetic signals (known thrust step, known dip, known descent speed).

  python3 indi_flight/bench/tests/test_auto_smoke_check.py
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import auto_smoke_check as C  # noqa: E402


def _g54(c_fn, t_ramp=10.0, edge=13.0, hover=0.5, z_fn=None):
    t = np.arange(0.0, 30.0, 0.01)
    tz = np.arange(0.0, 30.0, 0.01)
    z = np.full(tz.size, 5.0) if z_fn is None else z_fn(tz)
    return C.takeoff_g54(t, c_fn(t), t_ramp, edge, hover, tz, z)


def _ramp(t, t_ramp=10.0, edge=13.0, hover=0.5):
    return np.where(t < t_ramp, 0.0, np.where(t < edge, hover * (t - t_ramp) / (edge - t_ramp), hover))


def test_g54_smooth_ramp_passes():
    g = _g54(_ramp)
    # slope hover/3 s = 0.5/3 per s -> 0.1 s mean change = 0.01667 (3.33 % hover)
    assert abs(g["ramp_max_step"] - 0.5 / 30) < 1e-3, g
    assert abs(g["ramp_max_step_pct_hover"] - 100 / 30) < 0.3, g
    assert g["ramp_ok"] and g["edge_ok"] and g["dip_ok"] and g["n_ramp_points"] == 25, g


def test_g54_edge_step_fails():
    g = _g54(lambda t: _ramp(t) + np.where(t >= 13.0, 0.15 * 0.5, 0.0))
    assert not g["edge_ok"] and abs(g["edge_step_pct_hover"] - 15 - 3.33 / 2) < 1.0, g
    assert g["ramp_ok"], g


def test_g54_ramp_step_after_and_before_0p5s():
    def stepped(t0):
        return lambda t: _ramp(t) + np.where(t >= t0, 0.15 * 0.5, 0.0)
    g = _g54(stepped(11.0))  # 1.0 s after ramp start
    assert not g["ramp_ok"] and abs(g["ramp_max_step_t_s"] - 11.0) < 0.11, g
    g = _g54(stepped(10.3))  # 0.3 s after ramp start: inside the exempt first 0.5 s
    assert g["ramp_ok"], g


def test_g54_negative_steps_fail():
    # a 15 % DROP must fail too (abs); at the edge and inside the ramp
    g = _g54(lambda t: _ramp(t) - np.where(t >= 13.0, 0.15 * 0.5, 0.0))
    assert not g["edge_ok"], g
    g = _g54(lambda t: _ramp(t) - np.where(t >= 11.0, 0.15 * 0.5, 0.0))
    assert not g["ramp_ok"], g


def test_g54_dip_fails():
    dip = lambda tz: 5.0 - 0.5 * np.sin(np.pi * np.clip(tz - 13.0, 0, 1.0))  # noqa: E731
    g = _g54(_ramp, z_fn=dip)
    assert not g["dip_ok"] and abs(g["dip_m"] - 0.5) < 0.01 and g["edge_ok"] and g["ramp_ok"], g


def test_g54_takeoff_overshoot_and_bounce():
    t = np.arange(0.0, 30.0, 0.01)
    z = np.minimum(5.0, 1.0 * t)  # climbs to 5 m at t=5, edge 1, done 5, hold_end 20
    r = C.takeoff_overshoot(t, z, 1.0, 8.0, 20.0, 5.0)
    assert r["overshoot_ok"] and r["bounce_ok"] and abs(r["overshoot_m"]) < 1e-9, r
    r = C.takeoff_overshoot(t, z + np.where((t > 6) & (t < 7), 0.7, 0.0), 1.0, 8.0, 20.0, 5.0)
    assert not r["overshoot_ok"] and abs(r["overshoot_m"] - 0.7) < 1e-6, r
    r = C.takeoff_overshoot(t, z - np.where((t > 10) & (t < 11), 0.5, 0.0), 1.0, 8.0, 20.0, 5.0)
    assert not r["bounce_ok"] and abs(r["bounce_m"] - 0.5) < 1e-6 and r["overshoot_ok"], r


def _td(vz=0.5, tilt=2.0, lift=0.0, drop_landed=False, impact=None):
    t = np.arange(0.0, 10.0, 0.01)
    zz = np.where(t < 5.0, 5.0 - (5.0 - 0.0) * t / 5.0, 0.0) + np.where((t > 6) & (t < 7), lift, 0.0)
    v = np.full(t.size, vz)
    if impact:  # 1.2 m/s just before truth touchdown at t=5, while ground_contact is flagged late (t=5.6)
        v[(t > 4.85) & (t <= 5.0)] = impact
    la = np.where(t >= 5.6, 1, 0)
    if drop_landed:
        la[(t > 6) & (t < 6.2)] = 0
    return C.touchdown_check(t, zz, v, t, np.where(t > 5.5, tilt, 0.0), t, la, 1.0, 9.0, 0.0)


def test_g54_touchdown():
    r = _td()
    assert all(r[k] for k in ("vz_ok", "tilt_ok", "relift_ok", "landed_ok")) and abs(r["t_td_s"] - 4.95) < 0.011, r
    assert not _td(vz=1.0)["vz_ok"] and not _td(tilt=12.0)["tilt_ok"]
    r = _td(impact=1.2)  # late ground_contact must not hide the impact
    assert not r["vz_ok"] and abs(r["vz_contact"] - 1.2) < 1e-9, r
    assert not _td(lift=0.3)["relift_ok"] and abs(_td(lift=0.3)["relift_m"] - 0.3) < 1e-9
    assert not _td(drop_landed=True)["landed_ok"]


def test_g54_land_speed_and_rtl():
    assert C.land_speed_check(0.72, 0.7, 2.5, 2.0) == {"vz_ok": True, "disarm_ok": True}
    assert not C.land_speed_check(0.9, 0.7, 2.5, 2.0)["vz_ok"] and not C.land_speed_check(0.7, 0.7, 3.5, 2.0)["disarm_ok"]
    t = np.arange(0.0, 20.0, 0.1)
    sp = -np.where(t < 10, 10.0, 10.0 - (t - 10))  # NED: climb target 10 m, descend after t=10
    assert abs(C.descent_start(t, sp, 0.0) - 10.4) < 0.11
    assert C.rtl_height_error(t, sp, t, sp, 0.0, 10.0)["ok"]
    r = C.rtl_height_error(t, sp + 1.5, t, sp, 0.0, 10.0)
    assert not r["ok"] and abs(r["max_err_m"] - 1.5) < 1e-9, r


def main():
    t = np.arange(0.0, 10.0, 0.004)
    edge = 5.0
    thr = np.where(t < edge, 0.50, 0.58)  # known step 0.08
    tz = np.arange(0.0, 10.0, 0.02)
    h = np.full(tz.size, 5.0)
    d = (tz >= edge) & (tz < edge + 0.5)
    h[d] = 5.0 - 0.3 * np.sin(np.pi * (tz[d] - edge) / 0.5)  # known dip 0.3 m
    step, dip = C.handover_metrics(t, thr, tz, -h, edge)
    assert abs(step - 0.08) < 1e-6, step
    assert abs(dip - 0.3) < 0.01, dip
    # no dip when climbing
    _, dip0 = C.handover_metrics(t, thr, tz, -(5.0 + 0.1 * (tz - edge)), edge)
    assert dip0 == 0.0, dip0
    # descent at 0.7 m/s from 6 m
    tl = np.arange(0.0, 8.0, 0.02)
    hl = np.clip(6.0 - 0.7 * tl, 0, None)
    vz = np.where(hl > 0, 0.7, 0.0)
    v, n = C.mean_descent_vz(tl, -hl, vz)
    assert abs(v - 0.7) < 1e-9 and n > 100, (v, n)
    # transitions and tracking
    assert C.transitions(np.arange(6.0), np.array([1, 1, 2, 2, 2, 1])) == [(2.0, 1, 2), (5.0, 2, 1)]
    ts = np.arange(0.0, 4.0, 0.1)
    gt = np.zeros((ts.size, 3)); gt[:, 0] = 0.3; gt[:, 2] = -0.1
    sp = np.zeros((ts.size, 3)); sp[5:8] = np.nan
    r = C.track_err(ts, gt, ts, sp, 0.0, 4.0)
    assert abs(r["xy_rms"] - 0.3) < 1e-9 and abs(r["z_max"] - 0.1) < 1e-9 and r["n"] == ts.size - 3, r
    for f in (test_g54_smooth_ramp_passes, test_g54_edge_step_fails, test_g54_ramp_step_after_and_before_0p5s, test_g54_negative_steps_fail, test_g54_dip_fails):
        f()
    print("test_auto_smoke_check OK")


if __name__ == "__main__":
    main()
