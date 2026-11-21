"""Self-test of Q14 A (chatter needs ratio>20 AND line RMS>=5e-4) and Q15 A (skip item-2 windows within 3 s of a
nav_state change) in bench/g3_checks_key2.py. Run: python3 bench/tests/test_g3_checks_key2_q14_q15.py"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import g3_checks_key2 as K

FS = K.FS
T = np.arange(0, 60, 1 / FS)


def motors(amp, hz=70.0):
    rng = np.random.default_rng(1)
    u = 0.14 + rng.normal(0, 1e-6, (len(T), 4))  # tiny floor so peak/median >> 20 for any line
    u[:, 0] += amp * np.sin(2 * np.pi * hz * T)
    return u


def rates(nav_t, t0=40.0, t1=44.0):
    rng = np.random.default_rng(2)
    w = np.radians(rng.normal(0, 0.5, (len(T), 3)))
    b = (T >= t0) & (T < t1)
    w[b, 0] += np.radians(30.0) * np.sin(2 * np.pi * 30 * T[b])
    return K.osc_rates(T, w, nav_t)["p"]


def test_substep_line_not_chatter():
    m = K.chatter(T, motors(5e-4))["m0"]   # amp 5e-4 -> line RMS 3.5e-4 < 5e-4
    assert m["report_ratio"] > 20 and m["report_rms"] < K.DSHOT_STEP and not m["sustained"]


def test_line_above_step_is_chatter():
    m = K.chatter(T, motors(1e-3))["m0"]   # RMS 7e-4 >= 5e-4
    assert m["sustained"] and m["report_rms"] >= K.DSHOT_STEP and abs(m["report_f_hz"] - 70) < 1


def test_burst_after_nav_change_skipped():
    r = rates([39.5])                      # burst 40-44 s lies within 3 s after the change
    assert not r["sustained"] and len(r["skipped_windows_t"]) > 0


def test_same_burst_later_flagged():
    r = rates([30.0])                      # change 10 s earlier: burst windows not skipped
    assert r["sustained"]
    assert rates([])["sustained"]


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
