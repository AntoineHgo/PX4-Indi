# Q34 key 1: item 5 "A and B" and re-score of the 4 S230 pre-test runs (S243 owner amendment)

Key 1 only (indi_flight/bench/g3_checks.py). Key 2 not opened or changed. Nothing committed.

## Change
- bench/g3_checks.py: constants REC_B_FROM_S/REC_B_TO_S (line 88); item5_recovery (about lines 336-352): per event, A = old rule unchanged
  (now reported as pass_a); B = max 3-D position error <= 0.3 m (when a position reference exists) and max tilt error vs q_d <= 3 deg
  (when q_d exists) over every sample in [event + 5 s, event + 10 s], and the log must cover event + 10 s; pass = A and B. New row fields:
  pass_a, pass_b, b_max_pos_m, b_max_tilt_deg, log_covers_b_window. Docstring header (item 5 paragraph) updated. Items 1-4 and 6 untouched.
- Position error uses the same time-matched trajectory_setpoint and tilt the same q_d as part A (no new data source). NaN samples are excluded, as in A.

## Tests
- New bench/tests/test_g3_q34_key1.py (6 tests): passes both; fails A only; fails B on position only (0.4 m at event + 7 s); fails B on tilt
  only (4 deg at event + 7 s, both events); transient (tilt 6 deg or 0.8 m) in the first 5 s but clean in [5,10] -> PASS; window edges.
- Existing key-1 tests (test_g3_checks, _s226, q33_key1, align_s227, excursion_s186, line_trace_s191, refly_s212, g4_chatter_skip_key1): 37 passed,
  no expectation changed (none encoded a B-like rule). New file: 6 passed.
- Break-check: forced `good = good_a` (B term off): test_b_fails_on_position_only and test_b_fails_on_tilt_only FAILED (2 failed, 4 passed); restored, 6 passed.
- Run with PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /tmp/g3venv/bin/python -m pytest (the xonsh pytest plugin on this host breaks collection).

## Re-score (flags as SCORES.md: --run-json --mode position --wind [--sag] --skip-nav-change; outputs in q34_key1/)
| run | event | A | B max pos (m) | B max tilt (deg) | verdict | owner expected | match |
|---|---|---|---|---|---|---|---|
| indi_d0 | fault | pass (back 0.000 s, quiet 0.159 m) | 0.058 | 0.73 | PASS | PASS (0.058 m, 0.73 deg) | yes |
| indi_d0 | gust | pass (0.000 s, 0.067 m) | 0.052 | 0.64 | PASS | PASS | yes |
| pid_d0 | fault | pass (0.001 s, 0.077 m) | 0.057 | 0.49 | PASS | PASS | yes |
| pid_d0 | gust | pass (0.001 s, 0.095 m) | 0.074 | 0.56 | PASS | PASS | yes |
| indi_d262 | fault | FAIL (quiet 1.305 m) | 0.073 | 0.51 | FAIL (A) | FAIL (A) | yes |
| indi_d262 | gust | pass (0.001 s, 0.279 m) | 0.063 | 0.57 | PASS | PASS (0.063 m, 0.57 deg) | yes |
| indi_d283 | gust (no fault) | pass (0.000 s, 0.074 m) | 0.059 | 0.84 | PASS | not stated | n/a |

Item 5 overall per run: indi_d0 PASS, pid_d0 PASS, indi_d262 FAIL, indi_d283 PASS. Run overall unchanged vs SCORES.md (indi_d0 PASS; pid_d0 FAIL
item 4; indi_d262 FAIL items 4, 5; indi_d283 FAIL item 2). Items 1-4 and 6 JSON identical to raw_key1_*.json for all four runs.

Owner numbers reproduced (0.058 m / 0.73 deg, 0.063 m / 0.57 deg); no tuning. B never decides here: on these runs B passes with large margin everywhere,
so B has not been seen to fail on real data, only on the synthetic cases.
