"""M-1 air-relative wind drag + CLI conversion (bench/disturbance.py). Run: python3 bench/tests/test_disturbance_k110.py"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import disturbance as d  # noqa: E402

AF = d.load_airframe("quad5in", "/nonexistent.sdf")


def test_wind_profile_args():
    """Mutation (a): peak is the TOTAL wind, amp = peak - steady."""
    assert d.wind_profile_args(3.0, 9.0, 40.0) == (3.0, 6.0, 40.0)
    assert d.wind_profile_args(None, None, None) == (d.WIND_RAMP_TO, d.GUST_AMP, 0.0)
    assert d.wind_profile_args(2.0, None, None) == (2.0, d.GUST_AMP, 0.0)
    for bad in ((-1.0, None, None), (4.0, 3.0, None)):
        try:
            d.wind_profile_args(*bad)
        except ValueError:
            continue
        raise AssertionError(bad)
    st, am, dd = d.wind_profile_args(3.0, 9.0, 0.0)  # peak of the resulting profile is the requested total
    t_pk = d.WIND_RAMP_T + d.WIND_HOLD1_T + d.GUST_T / 2
    assert abs(d.wind_speed(t_pk, st, am) - 9.0) < 1e-12


def test_air_relative_drag():
    t = 8.0  # steady plateau, wind 4 m/s toward +x
    w = d.wind_speed(t, 4.0, 2.0)
    assert w == 4.0
    base = d.gust_x(t, AF, 4.0, 2.0, 0.0)
    assert d.gust_x(t, AF, 4.0, 2.0, 0.0, vel=(0.0, 0.0, 0.0))[0] == base[0]          # v = 0: legacy force
    assert abs(d.gust_x(t, AF, 4.0, 2.0, 0.0, vel=(4.0, 0.0, 0.0))[0]) < 1e-15         # moving with the air: no drag
    f = d.gust_x(t, AF, 4.0, 2.0, 0.0, vel=(1.0, 0.0, 0.0))[0]
    assert abs(f - AF.c_drag * 3.0 * 3.0) < 1e-12 and f < base[0]                      # faster vehicle, less force
    g = d.gust_x(t, AF, 4.0, 2.0, 90.0, vel=(0.0, -2.0, 0.5))                           # crossing: vector form, all axes
    rel = (0.0 - 0.0, 4.0 + 2.0, -0.5)
    n = math.sqrt(sum(x * x for x in rel))
    assert all(abs(g[i] - AF.c_drag * rel[i] * n) < 1e-9 for i in range(3))
    assert d.gust_x(t, AF, 4.0, 2.0, 0.0, vel=(-3.0, 0, 0))[0] > base[0]                # headwind speed adds drag


def test_pose_velocity():
    pv = d.PoseVelocity(min_dt=0.004)
    assert pv.update(1.0, (0, 0, 0)) is None
    assert pv.update(1.001, (9, 9, 9)) is None                                         # too close: ignored
    v = pv.update(1.01, (0.02, -0.01, 0.0))
    assert all(abs(a - b) < 1e-12 for a, b in zip(v, (2.0, -1.0, 0.0)))


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("PASS", name)
            except AssertionError as e:
                fails += 1
                print("FAIL", name, repr(e)[:200])
    sys.exit(1 if fails else 0)
