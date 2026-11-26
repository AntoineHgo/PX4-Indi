# P3B_KEY2: independent check of F-10 commits 2292882735 and 104508687b (range 1033890bb5..104508687b)

Verdict: PASS with findings (0 BLOCKER, 1 MAJOR, 3 MINOR). Read-only review; no builds or tests were run by me.

## 1. Behaviour neutrality
Method: comments stripped from old and new versions of every changed C/C++/rcS/airframe file and diffed; msg field/constant lists and yaml
structure (all keys except short/long) compared programmatically; old names grepped in the tree at 104508687b.

Non-comment, non-whitespace hunks (all are renames of private/local identifiers or function-parameter names; none changes runtime behaviour):
- indi_accel_control.cpp/.hpp: _lpf_um->_lpf_model_u, _native_cut/_native_hz/_native_f/_native_dev_count->_force_native_*, _u_buf/_um_buf->_mean_u_delay_buf/_model_u_delay_buf, _t_a_ff_prev->_a_ff_prev_time, _delay->_delay_samples, tb_s->blend_tc_s (private members, public setter parameter name only).
- indi_rate_control.cpp/.hpp: _dt_cmd->_torque_increment, local dt_cmd->torque_increment, tb_s->blend_tc_s. Public getTorqueIncrement() unchanged.
- IndiPosInjection.cpp/.hpp: parameter timestamp_sample_us->timestamp_us (4 uses in .cpp, 1 in .hpp, consistent).
- McIndiPosControl.cpp/.hpp: _q_time, _acc_time, _thr_time, _esc_time, _coll_meas, _hte, _hte_valid, _filter_hz, _filter_cut, ht, _param_indi_* -> descriptive names. The ParamFloat/ParamInt<px4::params::MC_INDI_*> template arguments are unchanged, so parameter names, defaults and ranges are unchanged.
- McIndiRateControl.cpp/.hpp: _measured_torque_model->_measured_torque.
- McIndiPosControl.cpp: PRINT_MODULE_DESCRIPTION text only (help output string, not behaviour).
- msg/*.msg: field names, types, order and constants identical (programmatic compare; the only diff in constants is trailing whitespace before the new comments). Comment text, units, [@frame]/[@invalid]/[@enum] tags changed; uORB topic and field names and the log topics are unchanged.
- yaml (pos and rate params): everything except short/long is structurally identical (name, default, min, max, unit, type, decimal unchanged). Parameter descriptions (short/long) were reworded: metadata text only.
- 4040_gz_quad5in: only the @name text and comments changed. rcS: comment only.
- Test files (*Test.cpp): licence header only, no assertion changed.
Rename consistency: grep of all old names at 104508687b found only unrelated hits (escChecksTest _esc_time, ekf2 timestamp_sample_us, and mc_indi_rate_control/IndiInjection.* whose timestamp_sample_us is correct because it is gyro time). No stale use. Local variable hover_thrust: no collision in McIndiPosControl.cpp (hte.hover_thrust is a struct field). Not verified by me: the compile and the 13/13 tests / 20-object disassembly claim (F10_FIX_S248.md); I only checked the renames statically.

## 2. Review coverage
| Review item | Status |
|---|---|
| BLOCKER IndiInjectionStep.hpp:39 design-note ref | applied |
| BLOCKER 4040_gz_quad5in:73 ref_airframe_model.md | applied |
| BLOCKER McIndiPosControl _coll_meas | applied (_collective_command, all uses) |
| Class B 8 hits (rcS D-SCHED, GZBridge A-14 x2, A-20, ESC A-37, SimScenarioPlayer x2-3) | applied (verified in diff) |
| MAJOR licence headers, 8 files | applied |
| MAJOR ActuatorTorqueMeasured CA_R_W_MAX | applied |
| MAJOR uORB doc standard, 4 msgs | applied (comment only) |
| MAJOR mc_indi_pos_control module description | applied, but see finding F1 |
| MAJOR _omega_ff_out comment | applied |
| MAJOR IndiPosInjection timestamp doc | applied |
| MAJOR "Copy of" line | applied (line removed) |
| MAJOR dt_cmd rename | applied |
| MAJOR public names (DT_MAX, INJ_RAMP, XY_P/XY_VP, uORB math-symbol fields, IndiRateFeedforward.timestamp_sample) x 5 rows | skipped, reason: not neutral (public param/field rename or behaviour change). Accepted, still open for the owner |
| MAJOR duplicate generator IndiInjection/IndiPosInjection | skipped, reason: needs refactor to src/lib, not neutral. Still open |
| Missed | none among BLOCKER/MAJOR |

## 3. Findings (regressions and residuals)
| file:line | severity | what | why |
|---|---|---|---|
| src/modules/mc_indi_pos_control/McIndiPosControl.cpp:1300-1305 | MAJOR | New module description says the stock position and velocity loops compute the acceleration "(no integrator)". The same file passes MPC_XY_VEL_I_ACC / MPC_Z_VEL_I_ACC to _control.setVelocityGains (line 619) and calls resetIntegral() at 5 sites, so a velocity integrator is wired. | New user-visible help text may misdescribe the code (I did not trace whether the INDI stage zeroes the integral output). Drop "(no integrator)" or confirm it. |
| src/modules/mc_indi_pos_control/IndiPosInjection.hpp:~37 | MINOR | "System identification excitation of mc_indi_pos_control (system identification, off by default)" repeats the phrase after the "bench" -> "system identification" substitution. | Mechanical replacement left a redundant sentence. |
| src/modules/mc_indi_rate_control/IndiInjectionStep.hpp (point{0} comment, ~line 60) and the "Run the INDI law" doc | MINOR | New 130+ character comment lines ("excitation added to the controller output, resp. to the rate setpoint"); the previous `u = c + d` shorthand was replaced by wordier text. Also McIndiPosControl.cpp/.hpp runIndiStage lines now exceed 140 chars after the ht -> hover_thrust rename. | PX4 style prefers short comments; astyle does not enforce width, so it passes the format check. |
| src/modules/mc_indi_rate_control/IndiInjectionStepTest.cpp:36 | MINOR | Still says "bench injection" (test file, untouched by the fix commits). | Residual wording from the review's "bench" class, not an id or path. |

## 4. Residual-id grep
`git grep -nE '\b(D-[A-Z0-9-]{3,}|S[0-9]{2,3}\b|K[0-9]{2,3}\b|Q[0-9]{2}\b|G[3-8]\([a-z]\)|indi_flight/|indi_project/)' 104508687b -- src msg ROMFS boards`
Hits: only false positives. 4014_s500 / 4015_holybro_s500 airframe names (S500), and boards/ nxp, agam, px4 fmu-v6xrt files (K66 MCU, FMUK66). Zero hits in the INDI, gz_bridge, sim_scenario_player, msg or posix ROMFS scope.
A second, INDI-scoped grep (indi_flight, indi_project, .md names, run_scenario, ref_airframe, design note, A-nn, G-letter refs, S-three-digit ids) returned no hits. The only "bench" hit is the test comment above.
