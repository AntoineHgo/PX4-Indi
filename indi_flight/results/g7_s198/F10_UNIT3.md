# F-10 unit 3: indi_accel_control.cpp / .hpp (comments and private names only)

Baseline HEAD, edits left in the working tree, not committed.

## Hits
Before: 14 (.cpp) + 13 (.hpp) per plan (about 27). After: 0 (P1-P4 grep, licence "COPYRIGHT OWNER" excluded). Also removed the numbered step prefixes ("1." .. "9.") that pointed into the spec.

## Renames (private members, in both files)
| old | new |
|---|---|
| `_g_t` | `_thrust_gain_mps2` (it is specific thrust per unit mean rotor thrust, not gravity, so not `_gravity_mps2` of the plan) |
| `_k_cmd` | `_mean_thrust_per_command` |
| `_tb`, `_b` | `_blend_time_constant_s`, `_blend_offset` (b is in normalised thrust units, not m/s^2) |
| `_j_diff`, `_j_diff_f` | `_jerk_difference`, `_jerk_difference_filtered` |
| `_u_idx` | `_delay_buffer_index` |
| `_lpf_f`, `_lpf_f_native` | `_force_lowpass`, `_force_lowpass_native` |
Not renamed (reach outside private members or are formulas): public `blend()`, `blendTimeConstant()`, `setThrustModel(g_t, k_cmd)` parameter names, Input/Output fields, locals (`u_model`, `a_ff`, `t_c`, ...), kMeanUSatLimit/kMaxOmegaFf constants (public).
Comments removed/rewritten: spec path in file header, ids D-GAP, D-ALTCTL-Z, D-AF-ALIAS, D-STAGE-STALE, D-T10-RESET, A14, A16, pre-freeze r1 F5/F6; "stage"/"stage rate" -> "control rate"/"loop"; "legacy path" -> what it does. No derivation lost (the formula block in the .hpp header is kept).

## Checks
(i) Source: gcc -fpreprocessed -dD -E -P token compare HEAD vs new with reverse rename: both files IDENTICAL (1469 and 413 tokens). PASS.
(ii) Object: build/f10_sitl via run.sh, baseline from HEAD sources (`ninja libIndiAccelControl.a`, `modules__mc_indi_pos_control`), then new. indi_accel_control.cpp.o, McIndiPosControl.cpp.o, IndiPosInjection.cpp.o: objdump -d --no-show-raw-insn, addresses/symbol names stripped, plus `size -A` .text: `diff -r` identical. PASS. Logs f10_u3_build_base.log, f10_u3_build_new.log.
(iii) `ninja -C build/px4_sitl_test unit-IndiAccelControl`, run: 61 tests PASSED (61 TEST/TEST_F in the unchanged test file). The baseline binary was not re-run separately. Log f10_u3_test_new.log. PASS.
(iv) `make format` (no further diff) and PX4_ASTYLE_FIX=0 check_code_style.sh on both files rc=0 (f10_u3_format.log). PASS.

## For the report
No derivation removed. Not done: rename of public `blend()` / `blendTimeConstant()` (unit test edit), setThrustModel parameter names.
