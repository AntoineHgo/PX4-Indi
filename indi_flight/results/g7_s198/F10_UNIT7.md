# F-10 unit 7: injection, watchdog, feed-forward enable, measured torque, McIndiRateControl (comments and private/test names only)

Baseline HEAD, edits left in the working tree, not committed. 13 files changed (35 insertions, 37 deletions), 23 files in scope.

## Hits
Before: 23 lines (margins_est.py paths/names x13, G7(b)/S196 x4, A18 x4, D-S3-FROZEN, D-S3-SPTO) plus "gate" in the project sense (9 lines). After: 0 (same grep). "frozen" (stuck rpm) is physical and kept. Comment density of the headers was already moderate; only the project-specific lines were reworded.

## Changes
- IndiInjection / IndiPosInjection (.cpp, .hpp, Test): reference to margins_est.py removed; stated in words: bins are log-spaced, 10 per decade, rounded to integer multiples k of 1/Tp (f = k / Tp); phases are Schroeder phases for equal power p = 1/K: phi_k = -2 pi sum_{l<k} (k - l) p_l.
- IndiInjectionStep.cpp: "gate" -> "break enabled / enable condition" wording; local `gate_open` -> `break_enabled`.
- IndiInjectionStepTest.cpp, IndiInjectionTest.cpp, IndiPosInjectionTest.cpp: G7(b)/S196 headings removed or replaced by "behaviour stated in the header"; gate wording replaced.
- IndiMeasuredTorqueTest.cpp: decision id removed. IndiRateFeedforwardGate.hpp, RateSetpointWatchdog.hpp, McIndiRateControl.cpp/.hpp: ids A18, D-S3-SPTO removed, "gate" -> "enable condition".

## Renames
| old | new |
|---|---|
| local `gate_open` (IndiInjectionStep.cpp) | `break_enabled` |
| test `MatchesMarginsEst` (IndiInjectionTest, IndiPosInjectionTest) | `MatchesReferenceMultisine` |
| test `RateSetpointBreakGating` | `RateSetpointBreakNeedsAllEnableConditions` |
| test `RateSetpointBreakGateClosingRestartsSequence` | `RateSetpointBreakDisabledInFlightRestartsSequence` |
| failure message string in that test `"gate " << g` | `"condition " << g` (test-only message, no assertion change) |
Not renamed: class/file `IndiRateFeedforwardGate`, its `allow()` and test suite name `IndiRateFeedforwardGateTest` (public names, file name; unit 9 type decision), members `_amp`, `_num`, `_freq`, `_t0_us` of the Injection classes (plan 1b lists them; not done within budget/risk-free scope).

## Checks (commands run from the repo root)
(i) Token compare: for each file `diff <(git show HEAD:$f | gcc -fpreprocessed -dD -E -P -x c++ -) <(sed <reverse renames> $f | gcc ...)`: 23 of 23 identical (f10_u7_tokens.log). PASS.
(ii) Objects: baseline built from HEAD sources of the 13 files, then new, `ninja -C build/f10_sitl modules__mc_indi_rate_control modules__mc_indi_pos_control` via indi_project/docker/run.sh (f10_u7_build_base.log, f10_u7_build_new.log). 10 objects of both modules: objdump -d --no-show-raw-insn with addresses, `<symbol>` and hex literals stripped, plus `size -A` .text: `diff -r` identical (f10_u7_objcmp.log). PASS.
(iii) Unit targets in build/px4_sitl_test (all pass, 0 failed; log f10_u7_test.log): IndiInjection 10, IndiInjectionStep 8, IndiPosInjection 12, IndiRateFeedforwardGate 6, IndiRateSetpointWatchdog 6, IndiTorqueStampTracker 6, functional-IndiMeasuredTorque 11. TEST/TEST_F count per test file equal to HEAD (source count, see command output in this unit). PASS.
(iv) Format: PX4_ASTYLE_FIX=0 Tools/astyle/check_code_style.sh on all 23 files, rc 0 each (f10_u7_format.log). PASS.

## For the report
No derivation removed. The margins_est.py formulas (log bins, Schroeder phase) are now stated in the comments in words and formula. Candidates for owner decision, not changed: public class/file name `IndiRateFeedforwardGate` and the `omega_ff` naming; the test target names.
