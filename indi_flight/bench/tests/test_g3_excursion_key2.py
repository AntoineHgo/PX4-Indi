"""Self-test of the S186 item-1 horizontal excursion (truth vs interpolated trajectory_setpoint) in bench/g3_checks_key2.py.
Run: python3 bench/tests/test_g3_excursion_key2.py"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import g3_checks_key2 as K

T = np.arange(0, 120, 1 / K.FS)
ST = np.arange(0, 120, 0.02)   # 50 Hz setpoint


def circle(t, r=20.0, wz=0.2):
    return np.stack([r * np.cos(wz * t), r * np.sin(wz * t)], 1)


def run(offset_fn, sp_nan=None, **kw):
    sp = circle(ST)
    if sp_nan is not None: sp[sp_nan(ST)] = np.nan
    pos = np.zeros((len(T), 3)); pos[:, :2] = circle(T) + offset_fn(T)
    pos[:, 2] = -10.0
    return K.excursion(T, pos, 10.0, 100.0, ST, sp)


def test_one_metre_offset_is_one_metre():
    r = run(lambda t: np.tile([1.0, 0.0], (len(t), 1)))
    assert abs(r["excursion_m"] - 1.0) < 1e-3 and r["excursion_sp_nan_frac"] == 0.0   # 20 m circle, 1 m offset


def test_six_metre_departure_fails_item1():
    def off(t):
        o = np.zeros((len(t), 2)); o[(t > 50) & (t < 55), 1] = 6.0; return o
    r = run(off); assert abs(r["excursion_m"] - 6.0) < 1e-2
    q = np.tile([1.0, 0, 0, 0], (len(T), 1)); pos = np.zeros((len(T), 3)); pos[:, :2] = circle(T) + off(T); pos[:, 2] = -10
    h = -pos[:, 2] + 0.0; h[:5000] = np.linspace(0, 10, 5000)[:5000] * 0 + h[:5000]
    ok = K.loc(T, q, pos, h, 100.0, 103.0, [], r)
    assert ok["pass"] is False
    ok1 = K.loc(T, q, pos, h, 100.0, 103.0, [], run(lambda t: np.tile([1.0, 0.0], (len(t), 1))))
    assert ok1["pass"] is True


def test_linear_interp_not_hold():
    # truth on the exact circle: with ZOH at 50 Hz the error would be ~ v*dt = 4 m/s*0.02 = 0.08 m; linear is ~1e-3
    assert run(lambda t: np.zeros((len(t), 2)))["excursion_m"] < 5e-3


def test_nan_samples_excluded_and_reported():
    r = run(lambda t: np.zeros((len(t), 2)), sp_nan=lambda t: (t > 40) & (t < 50))
    assert r["excursion_m"] < 5e-3 and 0.10 < r["excursion_sp_nan_frac"] < 0.12   # ~10 s of 90 s
    assert r["excursion_sp_outside_frac"] == 0.0


def test_no_usable_sample_is_skipped():
    r = run(lambda t: np.zeros((len(t), 2)), sp_nan=lambda t: t > -1)
    assert r["excursion_m"] is None and r["excursion_sp_nan_frac"] == 1.0
    assert K.excursion(T, np.zeros((len(T), 3)), 10, 100, None, None)["excursion_m"] is None


def test_beyond_setpoint_range_excluded():
    pos = np.zeros((len(T), 3)); pos[:, :2] = circle(T)
    r = K.excursion(T, pos, 10.0, 100.0, ST[(ST > 20) & (ST < 90)], circle(ST[(ST > 20) & (ST < 90)]))
    assert r["excursion_m"] < 5e-3 and abs(r["excursion_sp_outside_frac"] - 20 / 90) < 0.01


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"): f(); print("PASS", n)
