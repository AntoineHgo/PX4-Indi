"""Unit test of bench/scenario_overrides.py and the gust_x parametrisation. Run: python3 bench/tests/test_scenario_overrides.py"""
import copy
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import scenario_overrides as so  # noqa: E402
from scenarios import SCENARIOS  # noqa: E402
import disturbance as dist  # noqa: E402


def bad(sc, ov, frag):
    try:
        so.merge(sc, ov)
    except ValueError as e:
        assert frag in str(e), (frag, str(e))
        return
    raise AssertionError(f"accepted {ov}")


def test_merge_shallow_and_pure():
    sc = SCENARIOS["o1_lemniscate"]
    before = copy.deepcopy(sc)
    m = so.merge(sc, {"thrust_sag": {"scale": 0.85}, "motor_fault": {"segment": "traj", "motor": 1, "thrust_scale": 0.7}})
    assert m["thrust_sag"] == {"scale": 0.85} and m["motor_fault"]["motor"] == 1
    assert m["segments"] == sc["segments"] and sc == before          # input untouched
    # shallow: an override replaces the whole value, fields of the old value do not survive
    base = SCENARIOS["motor_loss_0"]
    assert "motor" in base["motor_fault"]
    m2 = so.merge(base, {"motor_fault": {"segment": "loss", "motors": [0, 1], "thrust_scale": 0.9}})
    assert "motor" not in m2["motor_fault"] and m2["motor_fault"]["motors"] == [0, 1]
    assert so.merge(sc, {}) == sc


def test_validation():
    sc = SCENARIOS["o1_lemniscate"]
    bad(sc, {"bogus": 1}, "unknown override key")
    bad(sc, {"thrust_sag": {"scale": 1.2}}, "thrust_sag")
    bad(sc, {"thrust_sag": {"scale": 0.8, "x": 1}}, "unknown field")
    bad(sc, {"motor_fault": {"segment": "nope", "motor": 0, "thrust_scale": 0.8}}, "segment 'nope'")
    bad(sc, {"motor_fault": {"segment": "traj", "motor": 4, "thrust_scale": 0.8}}, "motor index")
    bad(sc, {"motor_fault": {"segment": "traj", "motor": 0, "motors": [1], "thrust_scale": 0.8}}, "exactly one")
    bad(sc, {"erpm_loss": {"motor": 0, "start": "hold", "end": "traj"}}, "before")
    bad(sc, {"erpm_loss": {"motor": 0, "start": "traj", "end": "zz"}}, "segment 'zz'")
    bad(sc, {"wind": {"steady": 3.0}}, "needs disturbance")                       # scenario has no gust_x
    bad(SCENARIOS["gust_x"], {"wind": {"steady": 5.0, "peak": 4.0}}, "peak")
    bad(SCENARIOS["gust_x"], {"wind": {"speed": 5.0}}, "unknown field")
    bad(sc, {"disturbance": "gust_x", "dist_segment": "dist", "wind": {"steady": 3.0}}, "segment 'dist'")
    bad(sc, {"disturbance": "gust_x"}, "dist_segment")                              # default 'dist' absent in o1
    ok = so.merge(sc, {"disturbance": "gust_x", "dist_segment": "traj", "wind": {"steady": 3.0, "peak": 5.0, "dir_deg": 90.0}})
    assert so.wind_flags(ok) == ["--wind-steady", "3.0", "--wind-peak", "5.0", "--wind-dir", "90.0"]
    assert so.wind_flags(SCENARIOS["gust_x"]) == []


def test_window_validation_and_fault_list():
    sc = SCENARIOS["o1_lemniscate"]            # settle 3, traj 17.8, hold 3 = 23.8 s
    ok = {"erpm_loss": {"motor": 1, "start": "traj", "start_offset_s": 2.0, "duration_s": 2.0}}
    so.merge(sc, ok)
    for bad in ({"start_offset_s": 20.0}, {"duration_s": 0.0}, {"start_offset_s": -1.0}, {"motor": 4}):
        try:
            so.merge(sc, {"erpm_loss": {**ok["erpm_loss"], **bad}})
        except ValueError:
            continue
        raise AssertionError(f"accepted {bad}")
    gust = {"disturbance": "gust_x", "wind": {"steady": 2.0}}
    so.merge(sc, {**gust, "dist_segment": "traj"})
    try:
        so.merge(sc, {**gust, "dist_segment": "hold"})  # 13 s of profile from 20.8 s: beyond 23.8 s
    except ValueError as e:
        assert "window" in str(e)
    else:
        raise AssertionError("late wind accepted")
    two = [{"segment": "traj", "motor": 2, "thrust_scale": 0.8}, {"segment": "traj", "motors": [0, 1, 2, 3], "thrust_scale": 0.9}]
    m = so.merge(sc, {"motor_fault": two})
    assert so.fault_entries(m) == two and so.fault_entries(sc) == [] and len(so.fault_entries({"motor_fault": two[0]})) == 1
    try:
        so.merge(sc, {"motor_fault": []})
    except ValueError:
        pass
    else:
        raise AssertionError("empty fault list accepted")


def test_existing_scenarios_unchanged_without_overrides():
    # every shipped scenario: no wind key -> injector gets no extra argument
    assert all(so.wind_flags(sc) == [] for sc in SCENARIOS.values())


class AF:
    c_drag, cop_z = 0.5 * 1.225 * 0.012, 0.02


def test_gust_defaults_bit_identical():
    for i in range(0, 300):
        t = i * 0.1
        old_v = (0.0 if t < 0 else 3.0 * t / 2.0 if t < 2 else 3.0 if t < 12 else
                 3.0 + 6.0 * 0.5 * (1.0 - math.cos(2.0 * math.pi * (t - 12.0) / 1.0)) if t - 12.0 < 1.0 else 3.0)
        # same arithmetic as the original (t reduced stepwise), so compare the new function against the same stepwise form
        tt = t
        if tt < 2.0:
            v = 3.0 * tt / 2.0
        else:
            tt -= 2.0
            if tt < 10.0:
                v = 3.0
            else:
                tt -= 10.0
                v = 3.0 + 6.0 * 0.5 * (1.0 - math.cos(2.0 * math.pi * tt / 1.0)) if tt < 1.0 else 3.0
        assert dist.wind_speed(t) == v, t
        w = dist.gust_x(t, AF)
        assert w[0] == AF.c_drag * v * abs(v) and w[1] == 0.0 and w[2] == 0.0
        assert w == dist.gust_x(t, AF, 3.0, 6.0, 0.0)


def test_gust_parametrised():
    w = dist.gust_x(5.0, AF, 4.0, 2.0, 90.0)          # steady 4 m/s towards +y
    assert abs(w[0]) < 1e-12 and abs(w[1] - AF.c_drag * 16.0) < 1e-12
    assert abs(dist.wind_speed(12.5, 4.0, 2.0) - 6.0) < 1e-12   # peak total = steady + amp at mid gust
    f = dist.gust_x(5.0, AF, 4.0, 2.0, 30.0)
    assert abs(math.hypot(f[0], f[1]) - AF.c_drag * 16.0) < 1e-12 and abs(f[1] / f[0] - math.tan(math.radians(30))) < 1e-9


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
