"""K111 F-1: pure helpers behind the G3 runner hooks (timed eRPM loss split, motor_fault per-motor scale product).
python3 indi_flight/bench/tests/test_run_scenario_hooks.py   (exit 0 = pass, 1 = any failure)"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import run_scenario as rs  # noqa: E402


def test_split_durations_and_bitmask():
    for motor in range(4):
        sp = rs.erpm_loss_split(20.0, 3.0, 5.0, motor)
        assert [w for w, _, _ in sp] == ["pre", "loss", "post"], sp
        assert abs(sum(d for _, d, _ in sp) - 20.0) < 1e-12, sp  # sub-runs sum to the segment duration
        assert sp[0][1] == 3.0 and sp[1][1] == 5.0 and abs(sp[2][1] - 12.0) < 1e-12, sp  # loss starts at offset, lasts duration
        assert sp[0][2] is None and sp[2][2] is None and sp[1][2] == (1 << motor), sp  # bit only during the loss
    assert rs.erpm_loss_split(10.0, 0.0, 4.0, 2)[1][2] == 4  # motor 2 -> bit value 4


def test_fault_weak_motor_times_saturation():
    nom = {0: {"MIN": 100, "MAX": 1000}, 1: {"MIN": 100, "MAX": 1000}}
    cum = {0: 1.0, 1: 1.0}
    ents = [{"motor": 0, "thrust_scale": 0.64}, {"motors": [0, 1], "thrust_scale": 0.81}]  # weak motor 0, saturation on 0 and 1
    new = rs.fault_apply(cum, ents, nom)
    assert abs(cum[0] - 0.64 * 0.81) < 1e-12 and abs(cum[1] - 0.81) < 1e-12, cum  # product on the weak motor, saturation only on 1
    assert new[0] == {"MIN": 72, "MAX": 720}, new  # sqrt(0.64 * 0.81) = 0.72
    assert new[1] == {"MIN": 90, "MAX": 900}, new  # sqrt(0.81) = 0.9


def test_fault_incremental_and_rounding():
    nom = {2: {"MIN": 1, "MAX": 1999}}
    cum = {2: 1.0}
    n1 = rs.fault_apply(cum, [{"motor": 2, "thrust_scale": 0.5}], nom)
    assert n1[2] == {"MIN": 1, "MAX": int(round(1999 * math.sqrt(0.5)))} and isinstance(n1[2]["MAX"], int), n1
    n2 = rs.fault_apply(cum, [{"motor": 2, "thrust_scale": 0.5}], nom)  # a later segment multiplies onto the first
    assert abs(cum[2] - 0.25) < 1e-12 and n2[2]["MAX"] == int(round(1999 * 0.5)), (cum, n2)


if __name__ == "__main__":
    fails = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            try:
                fn()
                print("PASS", name)
            except AssertionError as e:
                fails += 1
                print("FAIL", name, repr(e)[:200])
    sys.exit(1 if fails else 0)
