# P3d: integrator wording and K2 MINORs (comment-only)

## Verdict
The stock velocity integrator accumulates inside update() but never reaches the commanded acceleration: it is zeroed before every update.

## Trace (src/modules/mc_indi_pos_control/McIndiPosControl.cpp unless noted)
- :617-619 passes MPC_XY_VEL_I_ACC / MPC_Z_VEL_I_ACC to setVelocityGains (gains non-zero).
- mc_pos_control/PositionControl/PositionControl.cpp:150: acc_sp_velocity uses `_vel_int` (read BEFORE the integral update).
- PositionControl.cpp:204: `_vel_int += vel_error * gain_i * dt` at the end of _velocityControl (only affects the NEXT update).
- McIndiPosControl.cpp:1071-1074: `if (want_indi) _control.resetIntegral();` before `_control.update(dt)` (:1079, retries :1093/:1100). want_indi = armed && (pos||vel||climb) (IndiStageMode.hpp:73).
- :1115-1118: resetIntegral() again after runIndiStage when _indi_active.
- :985-986, :1056, :1145: further resets (not flying, XY not controlled, else branch).
- So _vel_int is 0 when line 150 reads it, in every cycle where INDI is wanted. The accumulated value of one cycle is wiped before the next.
- INDI input: local_pos_sp.acceleration from _control.getLocalPositionSetpoint (:1103-1105) -> accel_command_pre_inject (:215) -> in.a_ref (:332). It contains only P/D and feed-forward terms.
- Airframe defaults: no MPC_*_VEL_I_ACC in ROMFS 4040_gz_quad5in nor indi_flight/bench/params/quad5in_indi_defaults.params; stock defaults apply, irrelevant since zeroed.
- Unverified: cycles with want_indi false (Bypass) were not traced; the branch is armed position/velocity/climb modes, so want_indi is expected true there.

## Comment changes (comments and help text only, no code)
- McIndiPosControl.cpp: module description (compiled in as help text only): "(their integrator is zeroed before each update)"; the :971 comment and the :1071 comment now state the zeroing.
- MINORs: redundant "system identification" in IndiPosInjection.hpp; "bench" in mc_indi_rate_control/IndiInjectionStepTest.cpp:36; rewrapped over-130 comment lines from 2292882735 in McIndiPosControl.cpp/.hpp, IndiInjectionStep.hpp, indi_accel_control.cpp.
- Not changed: msg files (field comments, long lines not astyle-checked).
