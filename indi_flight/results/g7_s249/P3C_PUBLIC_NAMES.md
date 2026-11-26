# P3c public names (S249): D-F10-PUBLIC-NAMES points (1), (2), (4)

Decision: indi_flight/DECISIONS.md "D-F10-PUBLIC-NAMES (S248)". Review: results/g7_s248/F10_WHOLE_BRANCH_REVIEW.md.
Points (3) (MC_INDI_XY_P/XY_VP kept) and (5) (multisine) are not part of this task.

## (1) Parameters: source check first

### MC_INDI_DT_MAX -> MC_INDI_INC_MAX
- Source: McIndiRateControl.cpp `_indi.setMaxIncrement(_param_mc_indi_dt_max.get())`; library
  src/lib/indi_rate_control/indi_rate_control.cpp:471 `torque_increment(i) = constrain(torque_increment(i), -_max_increment, _max_increment)`,
  then `t_cmd = constrain(t_fb + torque_increment, -1, 1)`.
- What it is: symmetric limit of the commanded torque increment (normalised torque, dimensionless) per control
  cycle and per axis. It is not a time step, not a duration. The review reading is correct.
- Decision: rename (the old name misleads: "DT" reads as time step). The decision stands.
- New name MC_INDI_INC_MAX (15 chars), same terms as the library setter setMaxIncrement. Same type float,
  default 1.0, min 0.01, max 1, decimal 2, increment 0.05, no unit.
- yaml short unchanged ("INDI maximum torque increment"); long now also states the output stays limited to [-1, 1].

### MC_INDI_INJ_RAMP -> MC_INDI_INJ_AMPR
- Source: McIndiRateControl.cpp:
  `inject_amp = (MC_INDI_INJ_PT == 1) ? _param_mc_indi_inj_ramp : _param_mc_indi_inj_amp`, passed as the amplitude
  to `_injection.setParameters(axes, inject_amp, ...)` (IndiInjection, sine multisine). With PT 1 the sine is added to the
  rate setpoint (rates_sp_inject, rad/s), with PT 0 to the torque (MC_INDI_INJ_AMP, normalised).
- What it is: amplitude of each sine component of the system identification excitation on the rate setpoint, rad/s.
  Nothing ramps. The review reading is correct.
- Decision: rename. New name MC_INDI_INJ_AMPR (16 chars, "amplitude, rate setpoint"; sibling of MC_INDI_INJ_AMP).
  Same float, default 0.05, min 0, max 1, unit rad/s, decimal 3, increment 0.01.
- yaml long now says "added to the rate setpoint".

### Not a behaviour change, but user visible
The parameter NAME changes (user visible: a value saved in a params file or on a vehicle under the old name is
not read and the default applies). Value, type, default, range, unit and all logic are unchanged.

### Edited
- src/modules/mc_indi_rate_control/mc_indi_rate_control_params.yaml (names, descriptions)
- McIndiRateControl.hpp/.cpp (`_param_mc_indi_inc_max`, `_param_mc_indi_inj_ampr`, one comment)
- docs/en/config_mc/indi_control.md (table row, link, anchor)
- indi_flight/report/01_inner_loop_design.md, 04_limits.md, 06_bringup_checklist.md (names; the yaml:NNN line
  references in 06 and 01 were not renumbered, the yaml shifted by 1 to 2 lines after the two long descriptions)
- No unit test, ROMFS, airframe (4040 or other) or src/ file sets or names these two parameters (git grep).
  Checked: zero hits for the old names in src, msg, ROMFS, Tools, boards, docs/en.

### Bench params files: NOT edited (older pinned binary knows only the old names)
Bench files under indi_flight/bench/ that set an old name:
- indi_flight/bench/params/quad5in_indi_defaults.params:31   `MC_INDI_DT_MAX 1.0`  ->  `MC_INDI_INC_MAX 1.0`
- MC_INDI_INJ_RAMP: no file under indi_flight/bench sets it.
- bench scripts (*.py, *.sh) under indi_flight/bench: no hit for either old name.
- indi_flight/bench/params/quad5in_indi_g1.params: no hit.
Old->new mapping for any later re-use with a new binary:
  MC_INDI_DT_MAX -> MC_INDI_INC_MAX
  MC_INDI_INJ_RAMP -> MC_INDI_INJ_AMPR
Evidence under indi_flight/results/ also carries the old names and is left untouched: 3443 files in about 60
campaign directories (run.json param dumps, *.params, g3_params.txt, the g2s_fly.sh/fly.sh scripts of freeze8_s181,
freeze9_s183, freeze10_s193, g2_*, stage5_s91_attbreak, xy_sweep_s183), plus design/ notes and DECISIONS/JOURNAL.
Any replay of them needs the same mapping.

## (2) IndiRateFeedforward.timestamp_sample: nothing to remove
msg/IndiRateFeedforward.msg has fields timestamp, omega_ff, valid only. `git log -S timestamp_sample -- msg/IndiRateFeedforward.msg`
returns no commit: the field never existed in this message (the review line 100 was wrong about this message).
The `timestamp_sample` that exist in IndiRateStatus (written McIndiRateControl.cpp:259) and ActuatorTorqueMeasured
(written :210) are written and read (staleness check at :235), so they stay. Bench readers of
indi_rate_feedforward (lag_chain.py) use `timestamp` only. No change made.

## (4) uORB field comments (field names unchanged)
msg/IndiPosStatus.msg: a_c, a_c_pre_inject, inject, a_f, t_f, t_c, t_c_applied, mean_u. msg/IndiRateStatus.msg: nu, inject.
Each trailing comment now names the symbol (where it is one), frame and unit, e.g.
`float32[3] t_f # [m/s^2] [@frame NED] Filtered measured specific thrust vector (t_f), thrust force per unit mass`.
mean_u comment now gives the expression u_i = (omega_i / MC_INDI_W_MAX)^2 (checked in McIndiPosControl.cpp:136-164).
No project ids in comments.

## Verification (docker px4-indi-sim via indi_project/docker/run.sh, timeouts 2400/1800 s)
- Format: `Tools/astyle/fix_code_style.sh --dry-run --formatted` on McIndiRateControl.cpp/.hpp: no output (clean).
  (yaml, msg, md are not C/C++.)
- Unit tests, build/px4_sitl_test (p3c_tests.log, p3c_tests2.log): all pass, 13/13 targets: IndiAccelControl,
  IndiInjection, IndiInjectionStep, IndiPosInjection, IndiRateFeedforwardGate, IndiRateSetpointWatchdog, IndiStageMode,
  IndiTorqueStampTracker, indi_rate_control_test (75 tests), EkfResetDetect, FailsafeSetpoint, SetpointExtrapolation,
  functional-IndiMeasuredTorque (11 tests). None of them names the two parameters.
- SITL build build/f10_sitl (p3c_sitl_build.log): ninja rc=0, 1457/1457 steps, bin/px4 linked. build/px4_sitl_default
  (pinned gate binary) untouched.
- Zero diff vs main in mc_rate_control, mc_att_control, mc_pos_control, control_allocator, control_allocation, commander.
- Not verified: no SITL flight with the new names (rename only; the generated parameter header maps the same
  members), NuttX targets not built, docs build (markdown link check) not run.

## Commits
- 8423db867b refactor(indi): rename two parameters and define uORB symbols (src, msg, yaml)
- second commit: docs/en + indi_flight/report + this record (hash in the final summary)
