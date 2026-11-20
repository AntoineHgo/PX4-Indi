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


def test_stabilized_hover_is_centre_stick():
    """S114: under MPC_THR_CURVE 0 centre stick is hover thrust whatever the hover value (S113 sent ~-0.73)."""
    for h in (0.137, 0.3, 0.5, 0.7):
        assert sp.neutral_sample("stabilized", hover_thr=h)["z"] == 500
        assert sp.neutral_sample("acro", hover_thr=h)["z"] == round((2 * h - 1) * 500 + 500)


def test_stabilized_round_trip_through_px4_curve():
    """The stick sent maps back, through an independent copy of mc_att_control throttle_curve, to the demand."""
    def px4_curve(stick, hover, tmin=0.08, tmax=1.0):   # interpolateNXY over {-1, 0, 1} -> {tmin, hover, tmax}
        return tmin + (stick + 1) * (hover - tmin) if stick < 0 else hover + stick * (tmax - hover)
    h = 0.137
    for t in (0.0, 0.3, math.pi / 4, 1.0, 2.5):
        s = sp.stick_sample(_pva_sine, t, "stabilized", hover_thr=h)
        want = h + 0.5 * sp.THRUST_GAIN * s["vz_up_demand"] / 3.0
        assert abs(px4_curve(s["throttle"], h) - want) < 0.003   # int rounding of z: 1/500 stick step
        assert abs(sp.stick_to_thrust(s["throttle"], "stabilized", h) - px4_curve(s["throttle"], h)) < 1e-9


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


def test_g51_steps():
    """S136: step table in profile time, per axis +A 0.5 s, -A 0.5 s, 0 for 2.5 s; throttle stays at hover."""
    for mode, a in (("acro", 1000), ("stabilized", 500)):
        assert sp.steps_duration() == 10.5
        for t, want in ((0.0, (0, a, 0)), (0.49, (0, a, 0)), (0.5, (0, -a, 0)), (0.99, (0, -a, 0)), (1.0, (0, 0, 0)), (3.49, (0, 0, 0)),
                        (3.5, (a, 0, 0)), (4.0, (-a, 0, 0)), (4.5, (0, 0, 0)), (7.0, (0, 0, a)), (7.5, (0, 0, -a)), (8.0, (0, 0, 0)), (10.5, (0, 0, 0))):
            assert sp.step_sticks(t, mode) == want, (mode, t)
        s = sp.stick_sample(lambda t: ([0] * 3, [0] * 3, [0] * 3), 0.2, mode, hover_thr=0.5, steps=True)
        assert (s["x"], s["y"], s["r"]) == (0, a, 0) and s["z"] == sp.neutral_sample(mode, 0.5)["z"]
    # default behaviour unchanged: x / y / r stay 0 without steps
    assert sp.stick_sample(_pva_sine, 0.3, "acro")["y"] == 0
