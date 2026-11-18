"""Self-test of the stick-profile generator on synthetic input (S81): known samples at known sim times."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import stick_profile as sp  # noqa: E402


def _pva_sine(t, vmax=1.5, w=2.0):
    """Synthetic climb: vz_up = vmax sin(w t); NED z velocity is minus that."""
    return [0, 0, 0], [0.0, 0.0, -vmax * math.sin(w * t)], [0, 0, 0]


def test_known_samples():
    w = 2.0
    for t, want_up in ((0.0, 0.0), (math.pi / (2 * w), 1.5), (3 * math.pi / (2 * w), -1.5)):
        s = sp.stick_sample(_pva_sine, t, "posctl")
        assert abs(s["vz_up_demand"] - want_up) < 1e-9
        assert abs(sp.expo(s["throttle"]) - want_up / 3.0) < 0.004   # PX4 expo of the applied stick gives the demand
        assert s["z"] == (500 if want_up == 0 else s["z"])
        assert (s["x"], s["y"], s["r"]) == (0, 0, 0)


def test_inv_expo():
    for d in (-1.0, -0.37, 0.0, 0.01, 0.5, 1.0):
        assert abs(sp.expo(sp.inv_expo(d)) - d) < 1e-9


def test_clip_and_modes():
    fast = lambda t: ([0, 0, 0], [0, 0, -9.0], [0, 0, 0])  # noqa: E731
    assert sp.stick_sample(fast, 0.0, "altctl")["z"] == 1000
    assert sp.stick_sample(lambda t: ([0] * 3, [0, 0, 9.0], [0] * 3), 0.0, "altctl")["z"] == 0
    assert sp.neutral_sample("posctl")["z"] == 500
    assert sp.neutral_sample("stabilized", hover_thr=0.5)["z"] == 500
    s = sp.stick_sample(_pva_sine, math.pi / 4, "acro", hover_thr=0.4)
    assert s["z"] == round((2 * 0.4 - 1 + sp.THRUST_GAIN * 1.5 / 3.0) * 500 + 500)


def test_zsine_o6_profile():
    from run_scenario import traj_pva
    from scenarios import ZSINE_O6
    pk = max(abs(sp.stick_sample(lambda t: traj_pva(ZSINE_O6, t), 0.05 * k, "posctl")["vz_up_demand"]) for k in range(400))
    assert abs(pk - 1.0 * math.pi / 2) < 0.02   # amplitude 1 m, w = pi/2 -> 1.571 m/s


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)
