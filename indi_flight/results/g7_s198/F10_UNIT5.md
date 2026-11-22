# F-10 unit 5: indi_rate_control.cpp / .hpp (comments and private names only)

Baseline HEAD, edits left in the working tree, not committed.

## Hits
Before: 8 (architecture.md path, D-S3-ATT-STEP, D-omega2 x2, D-S3-LANDED x2, D-YAW-INV, D-DEFAULTS-FW). After: 0. Also removed the step number prefixes ("1." .. "10.", "5b", "6c" ...) and the references "steps 3-5", "as 3-5" in comments; "stage pass-through" -> "filter pass-through"; "frozen/freezing" -> "held/holding" (3 places).

## Renames (private members, both files)
| old | new |
|---|---|
| `_t_act` | `_torque_actuator_model` |
| `_t_lpf` | `_torque_lowpass_state` |
| `_gain_k` | `_rate_bandwidth_gain` |
Not renamed: locals (`t_f`, `t_alloc`, `a_f`, `dt_cmd`, ... they follow the formula notation of the header and the logging getters), the other private members (`_t_f`, `_a_f`, `_dt_cmd`, `_t_fb_prev`, `_blend_tc`, `_meas_t_lpf` ...; the plan lists only the three), public API (`setGainK(gain_k)` parameter, `setActuatorBlendTimeConstant(tb_s)`, getters, `indiEffectiveGainK`).

## Checks
(i) Source: gcc -fpreprocessed -dD -E -P token compare of HEAD vs new with reverse rename: both files IDENTICAL (1125 and 582 tokens). PASS.
(ii) Object: baseline built from HEAD sources in build/f10_sitl (`ninja libIndiRateControl.a modules__mc_indi_rate_control modules__mc_indi_pos_control` via run.sh), then new. All 10 objects of the library and the two modules (20 files incl. size) compared; the 4 that include the header were rebuilt (library .o, McIndiRateControl, IndiInjectionStep, McIndiPosControl): objdump -d --no-show-raw-insn, addresses, `<symbol>` and hex literals stripped, plus `size -A` .text: `diff -r` identical. PASS. Logs f10_u5_build_base.log, f10_u5_build_new.log.
(iii) `ninja -C build/px4_sitl_test unit-indi_rate_control_test` and run: 75 tests from 8 suites PASSED. Log f10_u5_test.log. PASS.
(iv) `make format` (no further diff) and PX4_ASTYLE_FIX=0 check_code_style.sh on both files rc=0 (f10_u5_format.log). PASS.

## For the report
No derivation removed (the control law block in the .hpp header is kept; only decision ids and the doc path were dropped). Not done: renames of public names / locals as above.
