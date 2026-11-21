import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import g511_check as g

T = np.arange(0, 10, 0.01)


def zb_step(deg, ta=5.0):
    a = np.where(T >= ta, np.radians(deg), 0.0)  # tilt about x
    return np.stack([np.zeros_like(a), -np.sin(a), np.cos(a)], 1)


def test_tilt():
    assert g.tilt_jump_deg(T, zb_step(2.0), 5.0) > g.TILT_LIM_DEG
    assert g.verdict(True, g.tilt_jump_deg(T, zb_step(2.0), 5.0), 0.0, False) == "FAIL"
    j = g.tilt_jump_deg(T, zb_step(0.5), 5.0)
    assert abs(j - 0.5) < 1e-6 and g.verdict(True, j, 0.0, False) == "PASS"


def test_excursion():
    pos = np.zeros((len(T), 3)); pos[T >= 5.0, 0] = 0.6
    e = g.excursion_m(T, pos, 5.0)
    assert abs(e - 0.6) < 1e-9 and g.verdict(True, 0.0, e, False) == "FAIL"
    pos[T >= 5.0, 0] = 0.3
    assert g.verdict(True, 0.0, g.excursion_m(T, pos, 5.0), False) == "PASS"


def test_invalid_and_osc():
    assert g.verdict(False, 0, 0, False) == "INVALID"
    assert g.verdict(True, 0, 0, True) == "FAIL"
    cnt = np.where(T >= 5.0, 1, 0)
    ok, why, _ = g.validity(5.0, T, cnt, T, np.full(len(T), 4), [], "ekf_yaw")
    assert ok, why
    ok, why, _ = g.validity(5.0, T, cnt, T, np.where(T > 7, 14, 4), [], "ekf_yaw")
    assert not ok


def test_yaw():
    yaw = np.where(T >= 5.0, np.radians(5.0), 0.0)
    assert abs(g.yaw_change_deg(T, yaw, 5.0)[0] - 5.0) < 1e-6
    assert abs(g.sp_yaw_step_deg(T, yaw, 5.0) - 5.0) < 1e-6


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("ok", n)
