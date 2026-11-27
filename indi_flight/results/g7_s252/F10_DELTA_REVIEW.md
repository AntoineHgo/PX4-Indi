# F-10 delta review (0b1c6a26d1..HEAD, A_PATHS of make_fw_branch.sh)

Scope: `git diff 0b1c6a26d1 HEAD -- <A_PATHS>`: 39 files, 1347 insertions, 348 deletions. New files since the last review
that were read in full: IndiEscThrust.hpp, IndiEscThrustTest.cpp, IndiRateSetpointSource.hpp, IndiRateSetpointSourceTest.cpp.
IndiMeasuredTorque.hpp (+9) and IndiMeasuredTorqueTest.cpp (+263) are modified, not new (no IndiMeasuredTorque.cpp change in range).
Five pos_control files gained only the BSD header (EkfResetDetect, FailsafeSetpoint, SetpointExtrapolation, IndiStageMode and their tests).
Instruction files applied: control, parameters, messages (.github/instructions).

Grep: `git diff -U0 0b1c6a26d1 HEAD -- <A_PATHS> | grep -nE '^\+.*(\bD-[A-Z]|\b[AFGKQS][0-9]{1,3}\b|RC[0-9]|indi_flight|indi_project|owner|freeze|\bgate\b)'`
Hits: 3 lines (diff lines 415, 425, 426), all `G1`/`G2` INDI symbols in indi_rate_control.hpp formulas: accepted, no project id.
Manual check also found no remaining "bench", "np.unique", design-note or session references in added lines (the delta removes several).
Param names referenced in yaml/cpp/hpp all resolve to defined params (MC_INDI_INC_MAX, MC_INDI_INJ_AMPR renames consistent).

| file:line | severity | finding | suggested fix |
|---|---|---|---|
| src/lib/indi_accel_control/indi_accel_control.cpp:381-384 | MINOR | 4-line comment lists internal member names and the force expression (restates the next two lines). Only the last sentence (paths cancel, t_c = a_c - g) is non-obvious. | Keep "With invalid f_b the measured path is synthesised from the same delayed actuator signal and filter as the modelled path, so they cancel." |
| src/lib/indi_accel_control/indi_accel_control.cpp:96,172,379 | MINOR | `_last_um` is cryptic next to the renamed `_lpf_model_u` / `_model_u_delay_buf`. | Rename to `_last_model_u`. |
| src/modules/mc_indi_pos_control/McIndiPosControl.cpp:257 | MINOR | "excitation d ... (u == c)": d, u, c are not defined nearby. | "excitation on one NED axis, zero when MC_INDI_PINJ_AX is 0". |
| src/modules/mc_indi_pos_control/McIndiPosControl.cpp:415 | MINOR | "c is the commanded collective": symbol c undefined at this point. | "The collective is the commanded one, not measured; the measured mean u is passed separately (NaN: model path)". |
| src/modules/mc_indi_pos_control/IndiEscThrustTest.cpp:42 | MINOR | `kRpmMax` has no unit; `2.f *M_PI_F` spacing (astyle output, harmless). | `kRpmMax_rpm`; run make format if not already applied. |
| src/modules/mc_indi_rate_control/IndiRateSetpointSource.hpp:48 | MINOR | Only the first term is cast to uint8_t; the other terms promote to int and the return is the OR of int, so the cast covers only the first operand. Works, but reads as if the whole expression is cast. | `return (uint8_t)((attitude_enabled << 0) | (rates_enabled << 1) | ...);` |
| src/modules/mc_indi_rate_control/IndiInjectionStep.hpp:73 | MINOR | Doc line is over-long and names a code identifier (`!rate_sp_break_allowed`) instead of the condition; "break" is leftover project jargon (also the field name at :56). | "The excitation is 0 unless the rate setpoint is attitude controlled and fresh, and while the law reports a fault from the last cycle"; consider renaming to `rate_sp_injection_allowed`. |
| src/modules/mc_indi_rate_control/IndiMeasuredTorqueTest.cpp:483-492, 610-613 | MINOR | Hand-calculation block restates the arithmetic of the tests (derivation). The motor order/spin and sign convention lines are worth keeping. | Keep motor order, spin and the roll/pitch/yaw sign formulas; drop the scale derivation and the per-test arithmetic comments or reduce to the one-line result. |
| src/modules/mc_indi_rate_control/IndiMeasuredTorqueTest.cpp:494 | MINOR | Second anonymous namespace in the same file (first at :50); `kOmegaMax` has no unit. | Move `rpmFromSpeedRatio` into the first namespace; `kOmegaMax_radps`. |
| src/modules/mc_indi_rate_control/mc_indi_rate_control_params.yaml (MC_INDI_G1_R/P/Y long) | MINOR | New `long` ("Roll angular acceleration per unit of normalised torque.") restates `short` and `unit`; parameters guideline says omit `long` then. | Drop `long` of G1_R, G1_P, G1_Y. |
| src/modules/mc_indi_rate_control/mc_indi_rate_control_params.yaml, mc_indi_pos_control_params.yaml (INJ_*/PINJ_* short) | MINOR | "sysid" is an invented abbreviation in new `short` strings (guideline: plain words). | "INDI excitation axis" etc. (long already says system identification). |

No BLOCKER and no MAJOR rows. Messages: comments are unit/frame-tagged, state non-obvious conditions, no ids.
Headers: all new files carry the BSD header with 2026.

Not checked: build, make format, make check_format, docs/en parameter references (read-only review, nothing was run).

Verdict: PASS WITH FINDINGS (0 BLOCKER, 0 MAJOR, 11 MINOR)
