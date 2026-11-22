"""Self-test of g55_traj_limit with known answers (S197, Q25 B). Runs under pytest or `python3 test_g55_traj_limit.py`."""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import g55_traj_limit as g  # noqa: E402


def _grid(dur, dt=0.002):
    return np.arange(dt / 2, dur, dt)  # off the endpoints (central difference at t = 0 would see the clamp)


def test_circle_no_ramp_vrms_is_r_omega():
    tr = dict(shape="circle", r=2.0, z_amp=0.5, w=1.5, laps=2, ramp_s=0.0)
    v = g.v_rms(tr, _grid(g.metrics_dur(tr)))
    assert abs(v - 3.0) < 2e-3, v  # vertical sine does not count
    assert abs(g.h_lim(v) - 0.5) < 1e-12  # 0.125 * 3 = 0.375 < floor


def test_circle_with_ramp_known_integral():
    tr = dict(shape="circle", r=5.0, z_amp=0.75, w=1.0, laps=3, ramp_s=3.0)
    T = g.metrics_dur(tr)
    tc = T - 2 * tr["ramp_s"]
    exact = tr["r"] * tr["w"] * math.sqrt((2 * tr["ramp_s"] * (9 / 5 - 2 + 4 / 7) + tc) / T)
    v = g.v_rms(tr, _grid(T))
    assert abs(v - exact) < 2e-3, (v, exact)
    assert abs(g.h_lim(v) - 0.125 * exact) < 5e-4  # above the floor


def test_lemniscate_no_ramp_known_rms():
    tr = dict(shape="lemniscate", ax=5.0, ay=2.5, w=6.0 / math.sqrt(50.0), laps=2, ramp_s=0.0)
    exact = tr["w"] * math.sqrt(tr["ax"] ** 2 / 2 + 2 * tr["ay"] ** 2)  # 4.2426 m/s
    v = g.v_rms(tr, _grid(g.metrics_dur(tr)))
    assert abs(v - exact) < 3e-3, (v, exact)


def test_zero_horizontal_speed_gives_floor():
    tr = dict(shape="zmulti", harm=[1], amps=[1.0], w=math.pi / 2, laps=4, ramp_s=2.0)
    v = g.v_rms(tr, _grid(g.metrics_dur(tr)))
    assert v < 1e-9 and g.h_lim(v) == 0.5


def test_window_selection():
    t = np.arange(10.0, 20.0, 0.5)
    k1 = g.window_times(t, 12.0, 4.0)
    k2 = g.window_times(t, 12.0, 4.0, closed=True)
    assert k1[0] == 0.0 and k1[-1] == 3.5 and k2[-1] == 4.0


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f()
            print("PASS", n)
