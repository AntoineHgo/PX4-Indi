import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import g510_motors_key2 as k  # noqa: E402


def test_sat_time_known():
    t = np.arange(0, 20, 0.00125)
    m = np.full((len(t), 4), 0.5)
    m[(t >= 3.0) & (t < 5.5)] = 1.0          # 2.5 s all saturated
    m[(t >= 7.0) & (t < 8.0), 1] = 0.995     # 1 s on one motor only
    m[(t >= 10) & (t < 10.5)] = 0.98         # below threshold
    tot, longest, cov = k.sat_time(t, m, 2.0, 12.0, mode="all")
    assert abs(tot - 2.5) < 0.003 and abs(longest - 2.5) < 0.003 and abs(cov - 10.0) < 0.003
    tot, longest, _ = k.sat_time(t, m, 2.0, 12.0, mode="any")
    assert abs(tot - 3.5) < 0.003 and abs(longest - 2.5) < 0.003
    # window clipping
    tot, _, _ = k.sat_time(t, m, 4.0, 5.0, mode="all")
    assert abs(tot - 1.0) < 0.003
    # break check: threshold 1.01 gives zero
    assert k.sat_time(t, m, 2.0, 12.0, thr=1.01)[0] == 0.0


def test_att_recovery_known():
    t = np.arange(0, 6, 0.01)
    t_c = 2.0
    e = np.where(t < t_c, 35.0, 35.0 * np.exp(-(t - t_c) / 0.5))   # 5 deg at 0.5*ln(7)=0.973 s
    stay, first = k.att_recovery(t, e, t_c)
    assert abs(first - 0.973) < 0.011 and abs(stay - 0.973) < 0.011
    e2 = e.copy()
    e2[(t > 3.5) & (t < 3.6)] = 8.0                                 # re-excursion
    stay, first = k.att_recovery(t, e2, t_c)
    assert abs(first - 0.973) < 0.011 and abs(stay - 1.61) < 0.011
    assert k.att_recovery(t, np.full_like(t, 9.0), t_c) == (None, None)


def test_quat_and_tilt():
    a = np.radians(30)
    q = np.array([[np.cos(a / 2), np.sin(a / 2), 0, 0]])
    assert abs(k.tilt_deg(q)[0] - 30) < 1e-9
    assert abs(k.quat_angle_deg(q, np.array([[1.0, 0, 0, 0]]))[0] - 30) < 1e-9
    assert abs(k.quat_angle_deg(q, -q)[0]) < 1e-6


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f()
            print("ok", n)
