"""Self-test of key 1 (bench/g3_checks.py) item 5 "A and B" (GATES "Owner amendment S243", Q34): an event passes only if
A (t_rec <= 5 s and no position re-excursion > 0.3 m in (t_rec, t_rec + 5 s]) and
B (position error <= 0.3 m and tilt error vs q_d <= 3 deg on every sample in [event + 5 s, event + 10 s]). Synthetic truth, no flights.

    python3 -m pytest indi_flight/bench/tests/test_g3_q34_key1.py        (needs numpy, scipy, pytest; /tmp/g3venv)

Break-check (S243): the B term (good_b) was forced True in bench/g3_checks.py; the B-fail cases (test_b_fails_*) had to FAIL, then the
code was restored.
"""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_g3_q33_key1 import GUST, T0, make  # noqa: E402

win = lambda a, b: (lambda t: np.where((t >= a) & (t < b), 1.0, 0.0))   # noqa: E731


def ev(r, i):
    return r["item5_recovery"]["events"][i]


def test_passes_both_and_reports_b_maxima():
    r, _ = make(pos_err=lambda t: 0.8 * win(T0, T0 + 1.0)(t) + 0.8 * win(GUST, GUST + 1.0)(t))
    assert r["item5_recovery"]["pass"] and all(e["pass_a"] and e["pass_b"] for e in r["item5_recovery"]["events"])
    assert ev(r, 0)["b_max_pos_m"] == pytest.approx(0.0, abs=1e-6) and ev(r, 0)["b_max_tilt_deg"] == pytest.approx(0.0, abs=1e-6)


def test_fails_a_only():
    r, _ = make(pos_err=lambda t: 0.5 * win(T0 + 2.0, T0 + 3.0)(t))   # re-excursion inside the first 5 s; [5, 10] clean
    e = ev(r, 0)
    assert not e["pass_a"] and e["pass_b"] and not e["pass"] and not r["item5_recovery"]["pass"] and ev(r, 1)["pass"], e


def test_b_fails_on_position_only():
    r, _ = make(pos_err=lambda t: 0.4 * win(T0 + 7.0, T0 + 7.5)(t))   # 0.4 m at event + 7 s; A window [0, 5] clean
    e = ev(r, 0)
    assert e["pass_a"] and not e["pass_b"] and not e["pass"] and e["b_max_pos_m"] == pytest.approx(0.4) and e["b_max_tilt_deg"] < 3.0, e
    assert not r["item5_recovery"]["pass"] and ev(r, 1)["pass"]


def test_b_fails_on_tilt_only():
    r, _ = make(tilt=lambda t: 4.0 * win(T0 + 7.0, T0 + 8.0)(t) + 4.0 * win(GUST + 7.0, GUST + 8.0)(t))   # 4 deg at event + 7 s
    for i in (0, 1):
        e = ev(r, i)
        assert e["pass_a"] and not e["pass_b"] and not e["pass"] and e["b_max_tilt_deg"] == pytest.approx(4.0, abs=1e-3) and e["b_max_pos_m"] < 0.3, e
    assert not r["item5_recovery"]["pass"]


def test_transient_in_first_5s_but_clean_in_5_to_10_passes():
    r, _ = make(tilt=lambda t: 6.0 * win(T0 + 1.0, T0 + 3.0)(t) + 6.0 * win(GUST + 1.0, GUST + 3.0)(t))      # tilt 6 deg, 1..3 s
    assert r["item5_recovery"]["pass"], r["item5_recovery"]
    r, _ = make(pos_err=lambda t: 0.8 * win(T0, T0 + 3.0)(t) + 0.8 * win(GUST, GUST + 3.0)(t))              # 0.8 m, back at 3 s
    assert r["item5_recovery"]["pass"] and ev(r, 0)["t_recover_s"] == pytest.approx(3.0, abs=0.01), r["item5_recovery"]
    r, _ = make(mode="attitude", tilt=lambda t: 6.0 * win(GUST, GUST + 3.0)(t))                                  # attitude mode: tilt only, back at 3 s
    assert r["item5_recovery"]["pass"]


def test_b_window_edges_and_log_cover():
    r, _ = make(pos_err=lambda t: 0.4 * win(T0 + 10.2, T0 + 11.0)(t))     # just after the B window: not scored
    assert r["item5_recovery"]["pass"]
    r, _ = make(pos_err=lambda t: 0.4 * win(T0 + 5.1, T0 + 5.3)(t))       # just inside the B window start
    assert not ev(r, 0)["pass_b"]
