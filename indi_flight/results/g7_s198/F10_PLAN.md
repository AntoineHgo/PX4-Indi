# F-10 plan: comment and naming clean-up of the INDI firmware (Class A files)

Plan only, no source edited. File list confirmed in indi_flight/bench/make_fw_branch.sh (A_PATHS): the four
src dirs, 4 msg files, INDI lines of msg/CMakeLists.txt, src/lib/CMakeLists.txt, logged_topics.cpp, rc.mc_apps,
airframe 4040_gz_quad5in (+ airframes/CMakeLists.txt, boards/px4/sitl/default.px4board SIM line stripped).
51 tracked files in the four dirs (+ msg, airframe) = F10 file set, saved in the commands below.

## 1. Inventory

File set: `git ls-files src/lib/indi_accel_control src/lib/indi_rate_control src/modules/mc_indi_rate_control
src/modules/mc_indi_pos_control msg/ActuatorTorqueMeasured.msg msg/IndiPosStatus.msg msg/IndiRateFeedforward.msg
msg/IndiRateStatus.msg ROMFS/px4fmu_common/init.d-posix/airframes/4040_gz_quad5in`

Patterns (re-run with `grep -nE` / `grep -niE` over the set; zsh: put the list in a file and use `xargs grep`):
- P1 ids: `\b(D-[A-Z0-9-]+|A-?[0-9]{1,2}|S[0-9]{2,3}|K[0-9]{2,3}|Q[0-9]{1,2}|RC[0-9]+|G[3-8]|F-?[0-9]+)\b`
  (G1/G2 excluded by the [3-8] range; K/Q/RC had 0 hits; `A2`, `A14`, `A18` are anomaly ids, not axes. Check
  hits by eye: `A-?[0-9]` also matches nothing PX4-specific in these files, no false positive found.)
- P2 paths: `indi_flight|indi_project`
- P3 words (case-insens): `\b(owner|gate|freeze|stage|lesson|anomaly)\b`, with `COPYRIGHT OWNER` (licence header)
  removed: `| grep -vi 'COPYRIGHT OWNER'`. Remaining false-positive classes: "stage" in
  its normal control sense ("INDI stage", "stage rate" = the acceleration/rate loop; but the name IndiStageMode
  is project jargon, see section 1b), "freeze" = hold a filter state (physical, keep, but see "pre-freeze").
- Not caught by P1-P3, found by grep: "pre-freeze r1 F5/F6", "(architecture A)", "legacy path", "s8_impl_spec".
  Add P4 for the sweep: `pre-freeze|architecture A|legacy|r1 F|\bs[0-9]+_|S196|D-[a-z]`  (lower-case ids exist).

Totals (P1 + P2 + P3 lines, deduplicated): 159 lines. Ids by count: D-STAGE-STALE 12, A18 10, G7 8, D-F7-GROUND 8,
D-S3-LANDED 7, D-GAP 7, D-ALTCTL-Z 7, F3 6, D-T10-RESET 5, D-AF-ALIAS 4, S77/S196/F4/D-JFF-SOURCE 3 each, ~15 more
singles. P2 paths: 7 lines (4 airframe/headers + margins_est.py x4 in Injection headers/tests, s8_impl_spec.md,
architecture.md, ref_airframe_model.md). Words: stage 76, owner 36 (35 licence), gate 10, freeze 11, lesson 1.

| File (src/modules or src/lib) | lines | comment lines (%) | P1 | P2 | P3 | hits |
|---|---|---|---|---|---|---|
| mc_indi_pos_control/McIndiPosControl.cpp | 1315 | 174 (13) | 26 | 0 | 25 | 51 |
| mc_indi_pos_control/IndiStageMode.hpp | 108 | 30 (28) | 10 | 0 | 12 | 22 |
| mc_indi_pos_control/McIndiPosControl.hpp | 367 | 72 (20) | 7 | 0 | 11 | 18 |
| indi_accel_control/IndiAccelControlTest.cpp | 1657 | 131 (8) | 10 | 0 | 7 | 17 |
| indi_accel_control/indi_accel_control.cpp | 530 | 83 (16) | 9 | 0 | 5 | 14 |
| indi_rate_control/indi_rate_control_test.cpp | 2400 | 165 (7) | 12 | 0 | 2 | 14 |
| indi_accel_control/indi_accel_control.hpp | 282 | 129 (46) | 6 | 1 | 6 | 13 |
| msg/IndiPosStatus.msg | 33 | 1 (3) | 2 | 0 | 3 | 5 |
| mc_indi_pos_control/mc_indi_pos_control_params.yaml | 141 | n/a (descriptions) | 0 | 0 | 5 | 5 |
| indi_rate_control/indi_rate_control.cpp / .hpp | 493 / 395 | 96 (19) / 194 (49) | 3/2 | 0/1 | 1/1 | 4 / 4 |
| mc_indi_rate_control/IndiInjectionStepTest.cpp | 338 | 52 (15) | 1 | 0 | 3 | 4 |
| mc_indi_pos_control/IndiStageModeTest.cpp | 126 | 2 (2) | 2 | 0 | 1 | 3 |
| msg/IndiRateFeedforward.msg | 6 | 2 | 1 | 0 | 2 | 3 |
| IndiInjectionTest.cpp, IndiPosInjectionTest.cpp | 235 / 297 | 56 / 58 | 1/1 | 1/1 | 0 | 2 each |
| McIndiRateControl.cpp / .hpp, IndiRateFeedforwardGate.hpp, IndiInjectionStep.cpp, 4040_gz_quad5in | - | - | 0-1 | 0-2 | 0-2 | 2 each |
| all other files (CMake, Kconfig, 20 small files, 3 other msg) | | | | | | 0-1 (licence word only) |

Heaviest comment density (candidates to shorten even without ids): indi_rate_control.hpp 49%, indi_accel_control.hpp
46%, IndiPosInjection.hpp 60%, IndiInjection.hpp 60%, IndiRateFeedforwardGate.hpp/.cpp 72-78%, CMakeLists of
the four dirs (licence header only, ok). rc.mc_apps line 59 holds "D-start-fallback (F-1)". logged_topics.cpp,
msg/CMakeLists.txt, src/lib/CMakeLists.txt: no hit. Test names with ids: `A18*` (4+), `FrozenAtBypassA3A8`,
`FrozenAtE7EdgeSingleCycle`. 222 TEST/TEST_F in all; names read at the end of section 1b.

### 1b. Names worth renaming (private/local/test only; behaviour neutral)
| Now | Where | Proposed |
|---|---|---|
| `IndiStageMode` (file, class, test) | pos_control | `IndiAccelLoopMode` (needs file rename: CMake + includes; do last, own commit) |
| `_g_t` | indi_accel_control.hpp | `_gravity_mps2` |
| `_k_cmd` | accel hpp | `_command_gain` (check the comment first) |
| `_tb`, `_b` / `blendTimeConstant()`, `blend()` | accel hpp | `_blend_time_constant_s`, `_blend_offset_mps2` (b is a collective-gap offset; `blend()` is public, tests only -> unit test edit) |
| `_j_diff`, `_j_diff_f` | accel hpp | `_jerk_reference_unfiltered`, `_jerk_reference_filtered` |
| `_u_idx` | accel hpp | `_delay_buffer_index` |
| `_lpf_f` | accel | `_force_lowpass` |
| `_mean_u` | pos_control.hpp, accel | `_mean_collective_thrust` |
| `_f_b` | McIndiPosControl.hpp | `_force_body_n` (frame in name) |
| `_t_act`, `_t_lpf` | indi_rate_control.hpp | `_torque_actuator_model`, `_torque_lowpass_state` |
| `_gain_k` | rate hpp | `_rate_bandwidth_gain` |
| locals `t_f`,`a_f`,`t_c`,`a_c`,`a_ff`,`f` | .cpp (Vector3f, 2-3 uses each) | `torque_filtered`, `accel_filtered`, `torque_command`, `accel_command`, `accel_feedforward`, `force` |
| `dt` (16), `dt_s` vs `tb_s` mixed | various | keep `dt` in short blocks, otherwise `dt_s` |
| `omega_ff` (22), `u_model` (21), `a_ref` (15) | various | `rotor_speed_feedforward_radps`, `torque_model`, `accel_reference` (only where used outside a defined formula) |
| `_indi` (41 uses) | pos_control | `_accel_control` |
| `_num`, `_amp`, `_freq`, `_t0_us` | Injection*.hpp | `_num_periods`, `_amplitude`, `_base_frequency_hz`, `_start_time_us` |
| Test names `A18Circle...`, `FrozenAtBypassA3A8`, `FrozenAtE7EdgeSingleCycle` | accel test | drop the id, name the scenario: `CircleGivesAnalyticBodyRates`, `StepThenHoldGivesZeroJerk`, `FrozenWhenBypassed`, `FrozenForOneCycleOnEdge` |

Needs owner/route decision (reach logs, params files, bench): all `MC_INDI_*` / `MC_INDI_POS_*` parameter names
(e.g. `MC_INDI_W_MAX`, `MC_INDI_K_R/K_P/K_Y`, `MC_INDI_INJ_*`, `MC_INDI_ID_OK`); uORB fields `a_c`, `a_f`, `t_f`
style names in IndiPosStatus/IndiRateStatus/ActuatorTorqueMeasured (check the msg files for 1-2 letter names);
topic names; public accessors used by bench scripts; `SIM_GZ_GPS_DLY` (sim hook, already noted in D-G7-F-TEXT);
the `IndiStageMode` file name only if the bench greps it.

## 2. Task split (one implementing agent each, ~30 tool calls)
Common rules for every unit: change only comments, strings in params/msg descriptions, names listed; no executable
line change except the rename itself; no default, parameter name, uORB field, topic or logged name change; no
file rename outside unit 9. Keep comments that state unit, frame, physical reason, edge case; delete ids, paths,
history, derivations (move any real derivation to a list handed back to the owner for the report). Finish each unit
with `make format` on the touched files (astyle check as CI: `make check_format`), the unit-test target, and the
section 3 comparison. One commit per unit: `refactor(indi): ...` (behaviour neutral; names) or `docs(indi): ...`.

| # | Files | Change | Check |
|---|---|---|---|
| 1 | McIndiPosControl.cpp (51 hits) | strip ids/stage-jargon comments, rename locals | no unit target (module); SITL .text compare |
| 2 | McIndiPosControl.hpp + IndiStageMode.hpp + IndiStageModeTest.cpp (43 hits) | comments, member renames `_indi`, `_f_b`, `_mean_u`, test names | IndiStageModeTest + SITL .text |
| 3 | indi_accel_control.cpp + .hpp (27 hits, 46% comment hpp) | shorten comments, rename members of 1b | IndiAccelControlTest, SITL .text |
| 4 | IndiAccelControlTest.cpp (1657 lines, 17 hits) | ids in comments, test names `A18*`, `FrozenAt*`, local names | IndiAccelControlTest passes, same test count (`--gtest_list_tests` diff of count) |
| 5 | indi_rate_control.cpp + .hpp (8 hits, 49% comment) | doc paths, comment shortening, `_t_act`, `_t_lpf`, `_gain_k` | indi_rate_control_test + SITL .text |
| 6 | indi_rate_control_test.cpp (2400 lines, 14 hits) | ids, test names | indi_rate_control_test, same test count |
| 7 | mc_indi_rate_control: IndiInjection*, IndiPosInjection*, RateSetpointWatchdog*, TorqueStampTracker*, IndiRateFeedforwardGate*, IndiMeasuredTorque* (+ their tests), McIndiRateControl.cpp/.hpp, pos_control Injection files (~30 hits) | margins_est.py paths removed (state the formula in words), gate/freeze/owner words, 60-78% comment density | all small unit targets of the two modules + .text |
| 8 | yaml (two files, apply patch hunks of section 4 first), 4 msg files, rc.mc_apps (l.59), 4040_gz_quad5in (l.7-8), Kconfig | description text only, no name/default/unit change except where section 4 says | `make px4_sitl_default` param metadata diff (`parameters.json` before/after: only `long`/`short`/`unit` text), msg: generated headers identical except comments |
| 9 | optional, last: rename IndiStageMode -> IndiAccelLoopMode (file, class, CMake, includes, test) | pure rename, own commit | build + unit + .text compare |

## 3. Behaviour-neutral check
Before starting save a baseline from the clean HEAD (`git rev-parse HEAD` noted):
```
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi && B=build/px4_sitl_default
# baseline (once), build per the build-px4-linux skill; objects of INDI only:
find $B -path '*indi*' -name '*.o' | sort > /tmp/f10_objs.txt
mkdir -p /tmp/f10_base && for o in $(cat /tmp/f10_objs.txt); do
  objdump -d --no-show-raw-insn $o | grep -v '^$' | sed 's/^ *[0-9a-f]*:\t//' > /tmp/f10_base/$(echo $o | tr / _).dis; done
size -A $(cat /tmp/f10_objs.txt) | grep -E '\.text' | sort > /tmp/f10_base_text.txt
```
After each unit rebuild the same way into /tmp/f10_new and `diff -r /tmp/f10_base /tmp/f10_new` plus the
`.text` size diff. Expected result by unit type:
- comment-only unit: all .dis identical, .text sizes equal (also `-g0` recommended: compile with debug off, or
  strip with `objcopy -g`, because line numbers shift).
- rename of private members/locals: .dis identical except symbol names in mangled private member functions;
  use `objdump -d` without symbol names (the sed above drops addresses; add `| sed 's/<[^>]*>//g'`), .text size equal.
- test files are not in the module objects: compare the pass count instead:
  `ctest --test-dir $B -R Indi --output-on-failure` (or the unit-gtest binaries) -> same passed count, 0 failed.
Source-level shortcut for comment-only units (no build, run per file, must print nothing):
```
for f in $(git diff --name-only HEAD -- '*.cpp' '*.hpp'); do
 diff <(git show HEAD:$f | gcc -fpreprocessed -dD -E -P -x c++ - 2>/dev/null) \
      <(gcc -fpreprocessed -dD -E -P -x c++ $f 2>/dev/null) > /dev/null || echo "CODE CHANGED: $f"; done
```
(`-fpreprocessed -dD -E` strips comments but keeps tokens; use `-P` to drop line markers; for renames the diff must
equal exactly the planned rename: `... | diff - ... | grep '^[<>]'` reviewed against the rename list, or run a reverse
`sed` of the rename on the new file and diff to old.) Also: msg unit: `build/.../msg/topics_sources/*.h` regenerated identical
modulo comments; yaml: compare `build/px4_sitl_default/parameters.json` (or the generated params xml) keys, `default`,
`min`, `max`, `type` identical; `git diff --stat` shows no .px4board/CMake change except unit 9.
Also run `make check_format` and the project grep P1-P4 over the set: target 0 hits (except G1/G2/tau symbols).

## 4. Existing partial patch indi_flight/results/g7_s196/F_TEXT_PARTIAL_S196e.patch
186 lines, 18 hunks, only mc_indi_rate_control_params.yaml (the msg, licence-header and 4040 items of D-G7-F-TEXT are
not in it). `git apply --check` passes on the current tree (reverse fails, so not applied). Hunk review:
- Valid, fold into unit 8: removal of "Replaces MPC_*" wording and role statements, `unit:` additions (rad/s^2 x3,
  1/s, rad/s), "0.5x" -> "half their value", per-axis K_R/K_P/K_Y text, "in normalised torque" additions (hunks 1-3, 5-18).
- Needs re-edit before folding: (a) it collapses `long: |-` blocks into one very long line; PX4 yaml accepts
  folded text, but keep wrapping under ~120 columns with `>-`, not one 300-char line; (b) injection hunks keep
  "gate reopens" (word "gate" is a P3 hit): say "when the excitation conditions are met again"; (c) `d`, `c`, `u`
  symbols removed there is fine, check `unit:` is not an actual metadata change the owner wants decided (units
  reach the parameter metadata and QGC, so list as text-only but visible).
- Not in the patch, still to do: the 4040 comments (indi_flight/ paths), msg headers (IndiPosStatus P1 2, P3 3;
  IndiRateFeedforward 1+2), wrong publisher in IndiRateStatus.msg per DECISIONS.md, licence headers.
- Do not fold the DECISIONS reference itself into any comment.
Also: pos_control yaml has 5 P3 hits and is not covered by the patch.

## 5. Risks
- Comment removal can drop a real constraint: units check for "unit/frame/physical reason" before deleting, and
  hand back removed derivations for the report.
- Renaming `blend()`/accessors touches tests and possibly bench code: grep `indi_flight/` before renaming public names.
- zsh word splitting broke `grep $F` with a string variable: use `xargs` or arrays.
- McIndiPosControl.cpp is 1315 lines: split in two agents if unit 1 exceeds budget (hits are all in comments).
- `unit:` additions and yaml `long:` reformatting alter parameter metadata (not behaviour) - state it in the commit.
