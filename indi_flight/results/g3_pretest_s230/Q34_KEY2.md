# Q34 key 2: item 5 "A and B" (S243), re-score of the S230 pre-test

Key 2 only (bench/g3_checks_key2.py). Key 1 files were not opened. Rule: GATES.md "Owner amendment S243" (events per "Owner amendment Q33").

## Change
- `bench/g3_checks_key2.py` `recovery()`, lines 339-349 (docstring 295-297): `good_a` = old rule (t_rec <= 5 s, no position re-excursion > 0.3 m in (t_rec, t_rec+5 s]); `good_b` = on every sample with te+5 s <= t <= te+10 s, tilt vs q_d <= 3 deg and (position mode) 3-D position error vs the hover setpoint <= 0.3 m; a NaN sample fails closed. Event pass = A and B. New JSON fields per event: `pass_a`, `pass_b`, `b_max_pos_err_m`, `b_max_att_err_deg`. Break hook `KEY2_BREAK=item5b`. Items 1-4, 6, g4 chatter untouched.
- Attitude mode: B has the tilt term only (no position term there, as for A).

## Tests (PYTEST_DISABLE_PLUGIN_AUTOLOAD=1, /tmp/g3venv)
- New `bench/tests/test_g3_q34_key2.py`, 7 tests: passes both; fails A only; fails B on position only (0.5 m at +6..7 s); fails B on tilt only (4 deg at +7 s); same in attitude mode; >3 deg transient in the first 5 s, clean in [5,10] -> PASS; window edges (4 deg until +4.9 s passes, 4 deg at +9.5 s fails).
- Existing key-2 set (test_g3_checks_key2*.py, test_g3_excursion_key2.py, test_g3_q33_key2.py, test_g4_chatter_skip_key2.py, test_g3_align_s227.py): 45 passed with the new file.
- Expectation changed: `test_g3_checks_key2_s226.py::test_key2_item5_recovery_position_mode`, case `far` (0.5 m excursion at te+7..8 s): was event PASS (outside the 5+5 s A scope), now A passes and the event FAILS on B (that window is exactly B). Added `far2` (excursion at te+11..12 s) which still passes. No other expectation changed.
- Break-check: `KEY2_BREAK=item5b` -> 4 failed (B position, B tilt, B tilt attitude mode, window edges), 3 passed (the pass / A-only / transient cases do not depend on B). Restored: 7 passed.

## Re-score (flags as SCORES.md: --run-json --mode position, --wind, --sag per draw logic, --skip-nav-change)
Outputs: `q34_key2/<run>/run_NNN.json`, `q34_key2/raw_<run>.txt`, `q34_key2/args_<run>.txt`.

| run | event | A | B max pos m | B max tilt deg | verdict | owner expected | match |
|---|---|---|---|---|---|---|---|
| indi_d0 | fault@t0 | pass | 0.058 | 0.73 | PASS | PASS (0.058, 0.73) | yes |
| indi_d0 | gust | pass | 0.052 | 0.64 | PASS | PASS | yes |
| pid_d0 | fault@t0 | pass | 0.057 | 0.49 | PASS | PASS | yes |
| pid_d0 | gust | pass | 0.074 | 0.56 | PASS | PASS | yes |
| indi_d262 | fault@t0 | FAIL (re-excursion > 0.3 m) | 0.073 | 0.51 | FAIL | FAIL on A | yes |
| indi_d262 | gust | pass | 0.063 | 0.57 | PASS | PASS (0.063, 0.57) | yes |
| indi_d283 | gust (no fault) | pass | 0.059 | 0.84 | PASS | not stated | n/a |

indi_d283 telemetry events (reported-only, not gated): tel_loss and tel_frozen pass A and B (max 0.067 m, 1.72 deg).

## Unchanged vs old key2 outputs (`key2_<run>/run_NNN.json`)
Every JSON key except `item5_recovery` is byte-identical for all 4 runs (items 1-4, 6, chatter, skipped windows, max_dt_s). Within item 5, all old fields (t_back_s, re_excursion, max errors) are identical; only `pass` can change, and it did not for any event. Run-level verdicts unchanged: indi_d0 PASS, pid_d0 FAIL (item 4), indi_d262 FAIL (items 4, 5, chatter), indi_d283 FAIL (item 2).
