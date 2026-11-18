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



class _Cli:
    def __init__(self, out):
        self.out = out

    def cli(self, *a, **k):
        return self.out


def test_hover_thrust_valid_flag_and_px4_fallback():
    """K114 MAJOR: a non-valid or NaN HTE is replaced by MPC_THR_HOVER, clamped [0.05, 0.9] as mc_att_control."""
    assert rs.hover_thrust(_Cli("    hover_thrust: 0.14\n    hover_thrust_var: 0.0\n    valid: True\n")) == (0.14, True)
    assert rs.hover_thrust(_Cli("    hover_thrust: 0.31\n    valid: False\n")) == (0.31, False)
    assert rs.hover_thrust_used(0.31, False, 0.137) == 0.137
    assert rs.hover_thrust_used(0.14, True, 0.137) == 0.14
    assert rs.hover_thrust_used(float("nan"), True, 0.137) == 0.137
    assert rs.hover_thrust_used(None, True, 0.137) == 0.137
    assert rs.hover_thrust_used(0.02, True, 0.137) == 0.05
    assert rs.hover_thrust_used(0.95, True, 0.137) == 0.9


def test_stick_params_pin_curve_constants():
    """K114 MINOR 3: the inverse throttle curve constants are pinned in the run, not assumed from airframe defaults."""
    assert rs.STICK_PARAMS["MPC_THR_CURVE"] == 0
    assert rs.STICK_PARAMS["MPC_MANTHR_MIN"] == rs.stick_profile.MANTHR_MIN
    assert rs.STICK_PARAMS["MPC_THR_MAX"] == rs.stick_profile.THR_MAX


def test_hover_thrust_fallback_not_clamped():
    """K115 m2: PX4 clamps only the valid HTE value; MPC_THR_HOVER is used as is (att_control_main.cpp:246)."""
    assert rs.hover_thrust_used(0.31, False, 0.03) == 0.03
    assert rs.hover_thrust_used(None, True, 0.95) == 0.95
    assert rs.hover_thrust_used(0.03, True, 0.137) == 0.05


def test_hover_meta_fields_and_source():
    """K115 M1/M2: run.json hover fields for every run, with the source of the value used."""
    m = rs.hover_meta(0.14, True, 0.137)
    assert m == {"hover_thrust_estimate": 0.14, "hover_thrust_valid": True, "mpc_thr_hover": 0.137,
                 "hover_thr_used": 0.14, "hover_thr_source": "hte"}
    m = rs.hover_meta(0.31, False, 0.137)
    assert m["hover_thrust_valid"] is False and m["mpc_thr_hover"] == 0.137
    assert m["hover_thr_used"] == 0.137 and m["hover_thr_source"] == "mpc_thr_hover"
    assert rs.hover_meta(float("nan"), True, 0.2)["hover_thr_source"] == "mpc_thr_hover"


def test_main_wires_thr0_from_hover_meta():
    """K115 wiring: main() derives thr0 from hover_meta (HTE valid -> HTE, else param), no ad-hoc fallback."""
    import inspect
    src = inspect.getsource(rs.main)
    assert 'meta.update(hover_meta(ht, ht_valid, thr_hover_param))' in src
    assert 'thr0 = meta["hover_thr_used"]' in src
    assert 'ht or' not in src


def test_stick_profile_guard_matches_px4_range():
    """K115 m1/m2: hover 0.05-0.08 (valid for PX4) inverts; 0 and THR_MAX are rejected."""
    sp = rs.stick_profile
    for h in (0.05, 0.06, 0.08, 0.5, 0.9):
        assert sp.neutral_sample("stabilized", hover_thr=h)["z"] == 500
        assert sp.thrust_to_stick(0.3, "stabilized", h) > -1.0 - 1e-9
    assert sp.thrust_to_stick(0.03, "stabilized", 0.06) == 0.0   # below-hover thrust unreachable when hover <= MANTHR_MIN
    for h in (0.0, 1.0, -0.1):
        try:
            sp.thrust_to_stick(0.3, "stabilized", h)
        except ValueError:
            continue
        raise AssertionError(f"hover {h} accepted")


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
