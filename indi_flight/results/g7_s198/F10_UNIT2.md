# F-10 unit 2: McIndiPosControl.hpp, IndiStageMode.hpp, IndiStageModeTest.cpp (comments and private names only)

Baseline HEAD (unit 1 already committed). Edit left in the working tree, not committed. McIndiPosControl.cpp touched only for the member renames
(plus whitespace/line-break fixes forced by astyle after the longer names, and one trailing comment moved above its line).

## Hits (P1+P4, P2, P3 minus licence line)
- Before: about 43 (plan figure). After: 0 in all three files (no log strings in these files).
- Still open outside this unit: `IndiStageMode`/`StageMode`/`selectStageMode`/`kStageDt*` names and test suite name (unit 9), log strings in the .cpp (unit 1 list).

## Renames (private members, old -> new; also applied in McIndiPosControl.cpp)
| old | new |
|---|---|
| `_indi` | `_accel_control` |
| `_f_b` | `_specific_force_body_mps2` (it is the specific force in m/s^2, so not `_force_body_n` of the plan) |
| `_mean_u`, `_mean_u_valid` | `_mean_rotor_thrust`, `_mean_rotor_thrust_valid` (same wording as unit 1 local `rotor_thrust`; plan said `_mean_collective_thrust`) |
| `_a_ff` | `_accel_feedforward_mps2` |
Not renamed: uORB/library fields (`in.f_b`, `in.mean_u`, `in.a_ff`, `status.mean_u`), `_indi_active`, `_indi_reset_*`, `_stage_*`, `ht` parameter of runIndiStage
(declaration name only, cpp definition would need a change), all public/free function names.
IndiStageMode.hpp inline-function parameters/locals: `aref_ok` -> `accel_command_ok`, `n2` -> `norm_squared`, `ht` -> `hover_thrust`, `raw_dt` -> `raw_dt_s`.
Test: `SampleIntervalGate` -> `SampleIntervalLimitsHoldAndClamp` (suite name `IndiStageModeTest` kept, unit 9). Total 8 member/param renames + 1 test.

## Removed comment content (none was a real derivation; all ids/history)
Ids D-STAGE-STALE (a/b), D-F7-GROUND, D-ALTCTL-Z, D-T10-RESET, D-JFF-SOURCE, A18, T10, F1/F3/F4, "pre-freeze review r1", "owner rule F-1",
"architecture A"; "stage" -> "INDI loop" / "loop" in prose; "blend b" -> "blend"; "omega_ff" -> "rotor-speed feed-forward".
Kept: frames/units, ground-reaction reason for the modelled force, zero-thrust-vector reason, dt clamp limits, 5 Hz limit.

## Checks
(i) Source level: per file, `git show HEAD:f | gcc -fpreprocessed -dD -E -P -x c++ -` vs same on new file with the reverse rename (python regex) applied, tokens split on whitespace -> identical for all 4 files incl. McIndiPosControl.cpp. PASS.
(ii) Object level: build/f10_sitl, baseline built with HEAD sources restored (edits kept in scratchpad), then edits, `ninja -C build/f10_sitl modules__mc_indi_pos_control`
 via run.sh; McIndiPosControl.cpp.o (6998 lines) and IndiPosInjection.cpp.o (317): objdump -d --no-show-raw-insn, addresses, <symbol>, hex stripped, + `size -A` .text: `diff -r` identical. PASS.
 Logs: f10_u2_build_base.log, f10_u2_build_new.log.
(iii) Unit test: `ninja -C build/px4_sitl_test unit-IndiStageMode` then run the binary (run.sh, px4-indi-sim). Before 15 tests PASSED, after 15 tests PASSED (renamed test present). PASS.
 Logs: f10_u2_test_base.log, f10_u2_test_new.log.
(iv) Format: `PX4_ASTYLE_FIX=0 Tools/astyle/check_code_style.sh` on the 4 files (run.sh): all rc=0 (f10_u2_format_final.log; earlier logs show 3 alignment/line-length fixes in the .cpp). PASS.
(v) P1-P4 greps on the three files: 0 hits. PASS.

## Not done
IndiStageMode type/file/test-suite rename (unit 9); `docs/en/SUMMARY.md` and `docs/en/config_mc/indi_control.md` show as changed in git status but are not from this unit.
