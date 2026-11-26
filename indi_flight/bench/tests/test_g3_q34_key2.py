"""Q34 (S243) self-tests of the second key (bench/g3_checks_key2.py): item 5 = A and B. Synthetic data with a known answer.
A: t_rec <= 5 s and no position re-excursion > 0.3 m in (t_rec, t_rec + 5 s]. B: position error <= 0.3 m and tilt error vs q_d <= 3 deg on every
sample in [event + 5 s, event + 10 s]. Scenario times as test_g3_q33_key2.py (fault event t0 = 23 s, gust 35 s).
Break-check: KEY2_BREAK=item5b disables the B term, the three B-fail tests must then fail (results/g3_pretest_s230/Q34_KEY2.md).
Run: cd indi_flight/bench/tests && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q test_g3_q34_key2.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from test_g3_checks_key2_s226 import build, box
from test_g3_q33_key2 import rj_q33, dx, tilt, T0, GUST


def fault(r): return r["item5_recovery"]["events"][0]


def run(mode="position", **kw):
    return build(rj_q33("traj" if mode == "position" else "stick", "stabilized" if mode == "attitude" else None), mode, **kw)


def test_q34_key2_passes_both_a_and_b():
    e = fault(run(dpos=dx(T0, T0 + 3, 1.0)))                 # 1 m for 3 s: back at 3 s, then clean
    assert e["pass"] and e["pass_a"] and e["pass_b"] and e["b_max_pos_err_m"] < 0.05 and e["b_max_att_err_deg"] < 0.1


def test_q34_key2_fails_a_only():
    r = run(dpos=dx(T0 + 3.5, T0 + 4.0, 0.5))                # 0.5 m re-excursion at +3.5..4 s, back at 0 s -> inside (t_rec, t_rec+5]; [5,10] clean
    e = fault(r)
    assert not e["pass"] and not e["pass_a"] and e["re_excursion"] and e["pass_b"] and not r["item5_recovery"]["pass"]


def test_q34_key2_fails_b_on_position_only():
    r = run(dpos=dx(T0 + 6.0, T0 + 7.0, 0.5))                # A clean (t_rec 0, quiet window (0,5] clean); 0.5 m at +6..7 s
    e = fault(r)
    assert e["pass_a"] and not e["pass_b"] and not e["pass"] and 0.45 < e["b_max_pos_err_m"] < 0.55 and e["b_max_att_err_deg"] < 0.1


def test_q34_key2_fails_b_on_tilt_only():
    r = run(dtilt=tilt(T0 + 6.5, T0 + 7.5, 4.0))             # 4 deg at +7 s, position fine
    e = fault(r)
    assert e["pass_a"] and not e["pass_b"] and not e["pass"] and 3.9 < e["b_max_att_err_deg"] < 4.1 and e["b_max_pos_err_m"] < 0.05


def test_q34_key2_fails_b_on_tilt_attitude_mode():
    r = run("attitude", dtilt=tilt(T0 + 6.5, T0 + 7.5, 4.0))
    e = fault(r)
    assert e["pass_a"] and not e["pass_b"] and not r["item5_recovery"]["pass"] and e["b_max_pos_err_m"] is None


def test_q34_key2_tilt_transient_in_first_5s_clean_after_passes():
    r = run(dtilt=tilt(T0, T0 + 3.0, 6.0))             # 6 deg until +3 s (back at 3 s), clean in [5, 10]
    e = fault(r)
    assert e["pass"] and e["pass_a"] and e["pass_b"] and abs(e["t_back_s"] - 3.0) < 0.01 and e["max_att_err_deg"] > 5.9
    assert r["item5_recovery"]["pass"]


def test_q34_key2_b_window_edges():
    # 4 deg from 0 to +4.9 s: A sees it (t_rec 4.9 <= 5, no position re-excursion) but it is before the B window -> pass
    e = fault(run(dtilt=tilt(T0, T0 + 4.9, 4.0)))
    assert e["pass"] and abs(e["t_back_s"] - 4.9) < 0.01
    # 4 deg at +9.5..9.9 s is inside [5, 10] -> B fails
    e = fault(run(dtilt=tilt(T0 + 9.5, T0 + 9.9, 4.0)))
    assert e["pass_a"] and not e["pass_b"]
