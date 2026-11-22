# F-10 unit 1: McIndiPosControl.cpp (comments and local names only)

File: src/modules/mc_indi_pos_control/McIndiPosControl.cpp. Baseline HEAD feb48c3171. Edit left in the working tree, not committed.

## Hits (F10_PLAN P1+P4 patterns, P2, P3 minus the licence line)
- Before: P1/P4 26 lines, P2 0, P3 25 lines (51 total, matches F10_PLAN).
- After: P1/P2/P4 0. P3 2 lines, both inside log strings (executable text, not touched by rule of this unit):
  - l.275 `PX4_INFO("INDI stage cond 0x%02x ...")`
  - l.491 `PX4_WARN("INDI stage degraded ...")`
  They need a string change (and a one-word edit of the runtime log text) so they are left for the owner to decide.
  "stage" in identifiers (runIndiStage, pollStageInputs, StageMode, kStageDtMax ...) is member/type naming (unit 2).

## Renames (locals only, old -> new)
pollAcceleration: f -> specific_force, t -> sample_time.
runIndiStage: u -> rotor_thrust, u_sum -> rotor_thrust_sum, cut -> cutoff_hz, G -> accel_per_thrust_mps2,
a_c_pre_inject -> accel_command_pre_inject, a_ref -> accel_reference, t_c_applied -> thrust_command_applied,
coll_h -> hold_collective_raw, c_h -> hold_collective, coll_rs -> collective_raw and c_rs -> collective (reset block,
own scope), coll_stock -> stock_collective, coll -> collective_raw, c -> collective (bypass block).
Not renamed (parameters, members, uORB fields): ht, raw_dt, `status.a_c_pre_inject`, `status.t_c_applied`, `in.a_ref`, `out.*`.
One manual line break added in the `_indi.reset(...)` call of the reset block (long new names exceed astyle max-code-length 140);
whitespace only.

## Removed or shortened comment content
About 40 comments edited: ids (A18, A2, D-*, F2/F3/F4, T10, review r1 F1, key2 K1 ...) removed, "stage" -> "INDI loop"/"loop"
in prose, "freezes" -> "holds", "freshness gate" -> "freshness check". Kept: units, frames, edge cases, the 1.9 deg tilt spike reason.
Removed derivation/history (none was a real derivation; all history or cross-reference):
- D-AF-ALIAS rationale tag on the acceleration drain (the Hz/queue reasoning itself is kept).
- D-T10-RESET: kept the "1.9 deg tilt spike at a yaw reset" evidence, dropped the id.
- "same call as the bypass branch below" cross reference at the reset block (replaced by "reset() keeps the blend").
- D-GAP "keeps b" -> "keeps the blend" (b = collective-gap offset, a formula symbol of the library).
- Bypass comment "NaN: use u_model - b" shortened to "NaN: use the model path".
- "review r1 F1: ALTCTL on ground, stock thrust 0" -> "stock thrust is zero (altitude mode on the ground): straight up".
- "T9, removed" note on the integrator shift.
- "(key2 K1)" note on the hysteresis after Hold.

## Checks
(i) Source level. Commands (repo root, scratch files outside the repo):
    git show HEAD:$f | gcc -fpreprocessed -dD -E -P -x c++ - > head_stripped.cpp
    gcc -fpreprocessed -dD -E -P -x c++ $f > new_stripped.cpp
    reverse rename (python, regex `(?<![\w.])new(?!\w)` -> old, reset block mapped separately) on new_stripped.cpp -> new_rev.cpp
    diff head_stripped.cpp new_rev.cpp
  Result: empty after whitespace normalisation (`tr -s '[:space:]' '\n'` on both). Without normalisation 3 lines differ: the one
  manual line break above. PASS.
(ii) Object level. Separate build dir build/f10_sitl, all inside indi_project/docker/run.sh, timeout 3600, logs in
  indi_flight/results/g7_s198/f10_u1_*.log:
    run.sh -n f10base -t 3600 'cmake -S . -B build/f10_sitl -DCONFIG=px4_sitl_default -GNinja ...'
    run.sh -t 3600 'ninja -C build/f10_sitl modules__mc_indi_pos_control'   (baseline built at clean HEAD, RelWithDebInfo)
    then the same ninja after the edit.
  Both .o of the module (McIndiPosControl.cpp.o, IndiPosInjection.cpp.o): `objdump -d --no-show-raw-insn`, addresses and <symbol>
  and hex operands stripped, plus `size -A | grep .text` (per-section sizes). `diff -r base new`: identical disassembly
  (6998 + 317 lines) and identical .text section sizes. PASS.
(iii) Format: run.sh 'PX4_ASTYLE_FIX=0 Tools/astyle/check_code_style.sh src/modules/mc_indi_pos_control/McIndiPosControl.cpp'
  (astyle 3.1, what make check_format runs per file) -> clean. PASS (first attempt found one over-long line, fixed by the line break).
Not run: unit-test target (none for this file), full make check_format, build/px4_sitl_default untouched.
