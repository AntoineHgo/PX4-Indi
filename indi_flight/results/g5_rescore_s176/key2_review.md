# key2 review: G5 checkers vs GATES.md "Owner amendments S175" (commit 315cdad412)
Reviewer: independent second key. Code and spec read before README. No repo file edited except this one.

## Findings
BLOCKING: none.
MAJOR: none.
MINOR
1. g511_check.py:~182-193 (check_run wiring): the p95 subtraction (`excess = tilt - p95`) and the use of `exc_h` are only exercised
   through `verdict_s175` with hand-fed numbers. I mutated `excess = tilt - p95` to `excess = tilt`: all 6 tests in test_g511_check.py
   still PASS. The functions (noevent_tilt_jumps, noevent_p95, excursion_h_m) are tested; the glue that feeds them is not.
   Cheap fix: a check_run test on a tiny synthetic ULog, or assert tilt_excess_deg == tilt_jump_deg - noevent_p95_deg on the real json
   (true for s1: 0.7639 - 0.7747 = -0.0108).
2. g510_check.py:~115-120: if MPC_TILTMAX_AIR is absent from the log the limit silently stays 20 deg (stricter than MPC+5 = 50 deg
   at default). Conservative, documented in the docstring, not a lowered threshold in practice here (param is present), but the
   log-read branch in main() has no test (only analyse(tilt_lim_deg=) is tested).
3. g511_check.py noevent_tilt_jumps: no-event instants include takeoff/landing or manoeuvre segments if nav_state is constant;
   this can only raise the p95 (lenient). Observed s1: n=55, p95 0.775, max 0.951 deg, hover only, so no effect on current data.
   Exclusion uses event t_applied, not the counter instant t_a (differs by < 1 s here, window margin is 1 s + 9 s).
4. G5.9a "0.00 ms": output zeroing and the kill flag share the same publication tick (first output sample at the rise is already 0,
   last non-zero 1.25 ms before). The result is a true reading of the amended rule, but the margin is 0 by construction.

## Rule-by-rule (spec vs code)
- G5.2 g52_check.py:56-62: z band = max(0.02 d, 0.10 m), x 2 % d unchanged, truth, same window/release; old value kept as settle_s_2pct. OK.
- G5.9a g5_rows_check.py:190-215: reference = actuator_armed.kill rise (search from applied - 1 s), switch only as fallback,
  latency switch->kill and applied->kill reported as INFO; PASS limit 1 command period unchanged. OK.
- G5.10(a) g510_check.py:18,44-52,112-119: limit = MPC_TILTMAX_AIR (initial or last change before "sat") + 5 deg; alt loss 2.0, back 0.3 m / 5 s untouched;
  legacy 20 deg flag reported. OK (see MINOR 2).
- G5.11 xy g511_check.py:53-58,119-120: horizontal truth excursion <= 0.5 over [ta, ta+5] from pre mean, plus oscillation test; tilt jump reported only. OK.
- G5.11 yaw g511_check.py:98-101: (event tilt jump - p95 of same function at no-event instants, same flight, nav-state constant) <= 1 deg,
  3-D excursion 0.5 and oscillation unchanged. OK.
- G5.6 / G5.11-z: no code path, correctly "not tested". Q8 a A: kill uses firmware flag; EKF reset uses counter (unchanged).
- Unchanged parts: diff shows no threshold or window edits (LIM, TILT_LIM_DEG=1.0, EXC_LIM_M=0.5, SETTLE band, 1.25 ms all intact).

## Tests (Docker)
pytest: test_g52_check 6 passed, test_g5_rows_check 7 passed, test_g511_check 6 passed; test_g510_check.py (script style) OK.
Mutations (copy in container /tmp, repo untouched): z band floor removed -> test_g52 2 failed; G5.9a ref = switch -> test_g5_rows 1 failed;
G5.10 limit back to 20 deg -> test_g510 AssertionError; G5.11 p95 subtraction removed in check_run -> NOT caught (MINOR 1).

## Independent recomputation (own code on raw ulg, pyulog, no checker import)
| row | mine | checker | 
| G5.11 xy s1 (g511_fix_s161) t_a / horizontal truth excursion | 54.99375 s / 0.208595 m | 54.99375 / 0.208595 |
| G5.9a freeze s1 kill rise -> outputs 0 | rise 112.7000 s, outputs 0 at 0.00 ms (prev sample non-zero 1.25 ms before); applied->rise 40.0 ms | 0.00 ms; 40.00 ms |
| G5.2 posctl s1 z settle (band 0.10 m, d 1.9637 m) | 0.22325 s | 0.22325 s |
Tolerance accepted: 1e-4 m / 0.01 ms / one truth sample (1.25 ms). All within it.

## Verdict
key2 agrees on G5.2, G5.9a, G5.10(a), G5.11 (xy, yaw) as implemented; MINOR 1 recommended before the numbers count.
