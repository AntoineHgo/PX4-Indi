# G7(b) behaviour 30: excitation helpers break-check (S196)

Scope: IndiInjection (src/modules/mc_indi_rate_control/IndiInjection.cpp), IndiInjectionStep.cpp (same dir), IndiPosInjection (src/modules/mc_indi_pos_control/IndiPosInjection.cpp).
Tests: IndiInjectionTest.cpp, IndiInjectionStepTest.cpp, IndiPosInjectionTest.cpp. Production code unchanged.
Method as g7_s195/SURVIVOR_TESTS.md: one single-point mutation at a time (sed on the host, line numbers of HEAD), `make tests TESTFILTER='IndiInjection|IndiPosInjection'` (3 ctest targets) in the px4-indi-sim image via the project docker run.sh wrapper into build/px4_sitl_test, then `git checkout --` of the mutated file (all in g7_s196/mut.sh). Ids: I = IndiInjection.cpp, P = IndiPosInjection.cpp, S = IndiInjectionStep.cpp. "pre" = result against the tests as they were at HEAD; "post" = with the tests added here.

## Mutation table
Line numbers are identical in I and P except where noted (line 114: I `_started = false;` in update(), P `reset();`).
| id (I/P) | line | change | pre (HEAD tests) | post |
|---|---|---|---|---|
| 1 | 92 | phase sign `-2.0*pi*s` -> `+2.0*pi*s` | killed (MatchesMarginsEst, Gating) | killed |
| 2 | 101 | `d +=` -> `d -=` (sign) | killed (MatchesMarginsEst, Gating) | killed |
| 3 | 101 | `2*pi*f*t` -> `pi*f*t` (frequency) | killed | killed |
| 4 | 101 | amplitude x0.5 | killed | killed |
| 5 | 124 | delay `1e6f` -> `1e5f` (start timing) | I: SURVIVED; P: killed (RearmRestartsWindow only) | killed by DelayHoldsOffTheStart (+ DisarmedUpdateRestartsWindow) |
| 6 | 133 | stop `t >= N*Tp` -> `t >` | killed (Gating) | killed |
| 7 | 133 | window `N*Tp` -> `(N+1)*Tp` | killed | killed |
| 8 | 118 | `if (landed)` -> `if (false)` | killed | killed |
| 9 | 40 | axis range `axis > 3` -> `> 4` | SURVIVED (both) | killed by AxisOutOfRangeIsOff |
| 10 | 72 | per_decade in frequency spacing 10 -> 11 | killed | killed |
| 11 | 76 | upper-limit bin test removed | killed | killed |
| 12 | 76 | bin dedup `k == last_k` -> `k == last_k - 100000` (plain removal does not compile, -Werror unused) | not run on HEAD tests (no HEAD test has a collapsing period, so survives by construction) | killed by BinsAreUniqueForShortPeriod |
| 13 | 109 | `_axis == 0 \|\|` -> `false \|\|` in update() | SURVIVED | EQUIVALENT: axis 0 leaves _num = 0, same early return |
| 14 | 61 | `!(f_max > f_min)` -> `false` | SURVIVED | killed by InvalidRangeOrCountIsOff |
| 15 | 46 | unchanged-parameters test `n_periods == _n_periods` -> `true` | SURVIVED | killed by ParameterChangeRestartsOriginUnchangedKeepsIt, InvalidRangeOrCountIsOff |
| 16 | 58 | setParameters no longer restarts origin (`_started = false` removed) | SURVIVED | killed by ParameterChangeRestartsOriginUnchangedKeepsIt |
| 17 | 113 | `if (!armed)` -> `if (false)` | killed (I: Gating + 2 Step tests; P: Gating) | killed |
| 18 | 114 | disarm no longer restarts the window | I: killed by IndiInjectionStepTest only; P: SURVIVED (RearmRestartsWindow calls reset() by hand, never the disarmed update) | killed by DisarmedUpdateRestartsWindow (both) |
| 19 | 61 | `n_periods < 1` -> `< 0` | not run on HEAD tests (no test with n_periods 0) | killed by InvalidRangeOrCountIsOff |
| 20 | 61 | `!(period > 0.f)` -> `false` | not run pre | EQUIVALENT in defined behaviour: period 0 gives df = inf, k = 0, every bin skipped |
| 21 | 61 | `!(f_min > 0.f)` -> `false` | not run pre | EQUIVALENT in defined behaviour: guards only against log10(f_max/0) = inf cast to int (UB) |
| 22 | 40 | `axis < 0 \|\|` -> `false \|\|` | not run pre | killed by AxisOutOfRangeIsOff |
| S1 | Step 41 | `point == 1` -> `== 2` | killed (5 tests) | killed |
| S2 | Step 41 | `axis >= 0` -> `> 0` (PT1) | killed | killed |
| S3 | Step 50 | fault term of gate removed | killed (GateClosingRestartsSequence) | killed |
| S4 | Step 50 | `rate_sp_break_allowed` -> `true` | killed | killed |
| S5 | Step 51 | `in.armed && gate_open` -> `in.armed && (gate_open \|\| true)` (plain `in.armed` does not compile) | killed (2 tests) | killed |
| S6 | Step 52 | `y + d` -> `y - d` | killed | killed |
| S7 | Step 54 | law fed `rates_sp` instead of `rates_sp_applied` | killed | killed |
| S8 | Step 56 | PT1 `torque_inject.zero()` removed | SURVIVED | killed by ReusedOutputHasNoStaleFieldsAcrossBreakPoints |
| S9 | Step 57 | `torque_sp = pre + torque_inject` in PT1 | SURVIVED | EQUIVALENT: torque_inject was just zeroed |
| S10 | Step 59 | rates_sp_inject x2 | killed | killed |
| S11 | Step 65 | law fed `2*rates_sp` in PT0 | killed | killed |
| S12 | Step 69 | `point == 0` -> `point != 2` | SURVIVED | EQUIVALENT for the documented point values 0 and 1 (value 2 unspecified) |
| S13 | Step 69 | `axis >= 0` -> `> 0` (PT0) | killed (TorqueBreakUnchanged) | killed |
| S14 | Step 70 | torque path `in.armed` -> `true` | SURVIVED | killed by TorqueBreakNotInjectedWhileDisarmedOrLanded |
| S15 | Step 70 | torque path `in.landed` -> `false` | SURVIVED | killed by TorqueBreakNotInjectedWhileDisarmedOrLanded |
| S16 | Step 74 | `u = c + d` -> `c - d` | killed | killed |
| S17 | Step 51 | PT1 generator `in.landed` -> `false` | killed (Gating) | killed |
| S18 | Step 58 | `rates_sp_pre_inject = rates_sp_applied` | killed | killed |
| S19 | Step 75 | PT0 `rates_sp_pre_inject.zero()` removed | SURVIVED | killed by ReusedOutputHasNoStaleFieldsAcrossBreakPoints |
| S20 | Step 41 | `point == 1` -> `point >= 1` | SURVIVED | EQUIVALENT for the documented point values 0 and 1 |
| S21 | Step 76 | PT0 `rates_sp_inject.zero()` removed | not run pre (same class as S19) | killed by ReusedOutput... |
| S22 | Step 77 | PT0 `rates_sp_applied.zero()` removed | not run pre | killed by ReusedOutput... |
| S23 | Step 67 | PT0 `torque_inject.zero()` removed | not run pre | killed by ReusedOutput... (switch-off case) |

Counts (I1-I22, P1-P22, S1-S23 = 67 mutations; I12 and I19-I22 and S21-S23 were first run only after the tests were added, see "pre"):
- IndiInjection: 19 killed, 3 equivalent (I13, I20, I21), 0 survived. Real pre-fix survivors: I5, I9, I14, I15, I16 (5); I12/I19/I22 untested by construction.
- IndiPosInjection: 19 killed, 3 equivalent (P13, P20, P21), 0 survived. Real pre-fix survivors: P9, P14, P15, P16, P18 (5); P12/P19/P22 untested by construction.
- IndiInjectionStep: 20 killed, 3 equivalent (S9, S12, S20), 0 survived. Real pre-fix survivors: S8, S14, S15, S19 (4); S21-S23 untested by construction.
Total 22 + 22 + 23 = 67 mutations, 58 killed, 9 equivalent (none needs a firmware change), 0 survivors.

## Tests added (test files only)
- IndiInjectionTest.cpp and IndiPosInjectionTest.cpp (identical bodies per class): AxisOutOfRangeIsOff, DelayHoldsOffTheStart, InvalidRangeOrCountIsOff, BinsAreUniqueForShortPeriod (Tp 0.1 s, 1..60 Hz gives exactly 6 bins at 10..60 Hz, hand derived; bin amplitude 0.3 by DFT), ParameterChangeRestartsOriginUnchangedKeepsIt, DisarmedUpdateRestartsWindow. IndiInjectionTest.cpp also gained `#include <math.h>`.
- IndiInjectionStepTest.cpp: TorqueBreakNotInjectedWhileDisarmedOrLanded, ReusedOutputHasNoStaleFieldsAcrossBreakPoints (and `#include <math.h>`).
Expected values: 0.11957619297037093 (t = 3.7 s) is the margins_est reference already used by the existing tests; the rest follow from the headers (axis 1..3 else off, origin = first airborne cycle + delay, window = n_periods * period, restart on parameter change or disarm, zero when disarmed or landed).

## Final checks
- Unmutated: filter 'IndiInjection|IndiPosInjection' 3/3 pass; filter 'Indi|indi_rate_control|FailsafeSetpoint|SetpointExtrapolation|EkfResetDetect' 13/13 pass.
- astyle dry-run (`Tools/astyle/fix_code_style.sh --dry-run --formatted <3 test files>` in the docker image): no output, rc 0.
- `git status --short -uno`: only the three test files modified under src (indi_flight/STATE.md was already modified by someone else, not touched here).

## Reproduce
```
indi_flight/results/g7_s196/mut.sh <file> <line> '<sed s/// expr>' 'IndiInjection|IndiPosInjection'   # '-' as expr = unmutated run
bash indi_flight/results/g7_s196/_batch1.sh   # I/P 1-18 against the HEAD tests (_batch1.log; ran before the tests were added)
bash indi_flight/results/g7_s196/_batch2.sh   # I/P survivors and 19-22 with the new tests (_batch2.log)
bash indi_flight/results/g7_s196/_batch3.sh   # S1-S20 against the HEAD tests (_batch3.log)
bash indi_flight/results/g7_s196/_batch4.sh, _batch5.sh, _batch6.sh   # S survivors with the new tests (_batch4.log)
```
The _batch scripts are the mutation lists as run; re-running _batch1/_batch3 against the current tree gives the "post" column, not "pre".
mut.sh does `git checkout -- <file>` on the file it is given: never pass a test file to it (it reverted a freshly written test once during this run; the test was rewritten and re-verified in batch 6).

## Unverified
- The pre column for I12/I19-I22 and S21-S23 is by construction (no HEAD test exercises them), not from a run; their post result is a run.
- _batch1.sh holds I12/P12 in the plain-removal form, which does not compile (-Werror); the valid form is in _batch2.sh. _batch4.log was produced before the S23 switch-off assertion existed; S23 was re-run in batch 6 (log not saved).
- Equivalence of I13/I20/I21/S9/S12/S20 (and the P twins) is by reading, not by test.
- Per-test failing lists are only in the _batch logs.
