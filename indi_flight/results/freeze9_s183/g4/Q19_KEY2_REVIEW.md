# Q19 independent review (key 2 on the metric change), 2026-11-21

Spec: GATES.md "Owner amendment S183" (Q19 test-definition fix). Code reviewed against the originals
bench/g3_checks.py, bench/g3_checks_key2.py, g4_gate_s169/rescore_s175.py and rescore_key2_s175.py.
Break-check driver: scratchpad/brk.py (scipy is not installed on the host; a numpy shim of periodogram/detrend in
scratchpad/shim was used for key 1 only; key 2 and the guard are pure numpy).

## Verdicts
| script | verdict |
|---|---|
| g3_checks_q19.py (key 1 wrapper) | OK (2 MINOR) |
| rescore_key1_q19.py | OK (1 MINOR) |
| rescore_key2_q19.py | OK (1 MINOR) |
| guard_q19.py | OK as a data producer; DEFECT as the guard: the fail rule is not implemented anywhere (BLOCKING, F1) |

## Findings
- F1 BLOCKING, guard_q19.py:38 (and absent elsewhere): no code compares INDI with PID. The four files only emit data
  (guard_indi.jsonl, g4_pid/guard_pid.jsonl). The comparison and its metric are undefined, and the choice flips rows.
  Transitions match by "from->to#nth" (guard_q19.py:28), not by time: correct, and the pair lists are equal in all 4
  PID runs. But on the existing data, with `any_rms` (max over all overlapping windows) and strict INDI > PID, 9 of 12
  transitions FAIL, mostly at 1.0e-4..5e-4 (e.g. hover_harsh_s1 4->14: INDI 1.39e-4 vs PID 1.02e-4, far below the
  5e-4 chatter floor). With `flagged` (ratio > 20 and RMS >= 5e-4) only INDI has flagged windows (5.0e-4..5.3e-4 at
  17->4 and 14->18; PID none), which also FAILS those rows. The owner text does not say which of the two, nor a
  tolerance or floor. Needs an explicit rule before G4_SCORES uses it (suggest asking: "line RMS = max over flagged
  windows, floor 5e-4, strict >" vs "max over all"). 14->18 (land) overlaps the Q18 land skip; the guard reports it
  anyway, which is what Q18 asks.
- F2 MINOR, g3_checks_q19.py:7-14: the nav list is handed to the chatter call through module globals and `_t0` is the
  grid start of the last `uniform()` call (the command grid, since the chatter call follows it). Correct today
  (verified: skip at the right absolute time, see break check); fragile if g3_checks.evaluate reorders its calls.
- F3 MINOR, g3_checks_q19.py:16: with no `--skip-nav-change` flag nav_changes is None and the skip is silently off.
  rescore_key1_q19.py:60 passes the flag, so no effect now.
- F4 MINOR, rescore_key1_q19.py:67: the "skipped windows" column counts rate windows only; the skipped command
  windows (the Q19 change) are not shown (the JSON has them under command_chatter.motors[].skipped_windows).
- F5 MINOR, rescore_key2_q19.py (all): the Q18 land skip is not composed into these two scripts (they are the
  S175-style scorers; Q18 lives in bench/g4_chatter_skip_key1/2.py, which have no Q19 skip). Moot on every current
  run: the airborne span ends before ground contact (q18/key1_indi_18_gate.md: 0 skipped land windows, 18/18).
  Neither Q18 nor Q19 moves a chatter verdict: 0 CHATTER rows before and after, both keys.
- Time base, OK: key 2 and the guard use vehicle_status.timestamp and actuator_motors.timestamp, both absolute, with
  t_off = grid start (rescore_key2_q19.py:84, guard_q19.py:24,33). Key 1 uses start_timestamp-relative stamps for both
  (actuator_motors timestamp_sample, <= few ms off vehicle_status.timestamp, negligible vs 3 s).
- First nav_state, OK: np.diff form, so the initial value is not a change; the 4->17 take-off change (c ~30 s) is before
  the airborne span (starts ~33.8 s) and c+3 < span start, so it skips nothing; guard lists it with n_win 0.
- Nothing else changed, OK: thresholds (ratio 20, DSHOT_STEP 5e-4), 4 s windows, 1 s hop, 20-100 Hz, +-2 Hz line RMS
  are the original code (K.psd_windows / k1.line_detector called unchanged). Skip overlap test `ta < c+3 and ta+4 > c`
  matches Q15. The guard windows use the same overlap test (7 windows x 4 motors = 28 per transition).

## Break check (synthetic, 800 Hz, 120 s, take-off at 5 s, motor 1 + 0.03 sin(2 pi 30 t) = 0.021 RMS)
| case | key 1 chatter sustained | key 2 chatter sustained |
|---|---|---|
| burst 60-63 s, nav change at 60 s (inside skipped windows) | False (7 windows skipped) | False (0 flagged) |
| same burst, no nav change | True | True (6 flagged) |
| burst 80-83 s, nav change at 20 s (outside) | True | True |
| burst 70-80 s, nav change at 60 s | True | True |
| burst 58-70 s, nav change at 60 s (spills past the skip) | n/a | True (windows from 63 s count; correct) |
Guard (fake ULog driven through guard_q19.one): burst in the skipped window of 4->14#1: INDI flagged 0.0211 at 30.0 Hz,
any_rms 0.0211; PID synthetic without burst: flagged None, any_rms 4.8e-4. So INDI 0.0211 > PID 4.8e-4 would FAIL the
row by the spec rule; the same burst outside the skipped windows gives guard flagged None (not reported, counted by
the detector instead). The comparison itself had to be done by hand (F1).
