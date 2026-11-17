# T122 hover slice S60 (stage 5, first code)

## Done
- `src/lib/indi_accel_control`: `Input::accel_only` entry (A14): no p/v required, a_c = a_ref. +5/-4 lines hpp/cpp; test `AccelOnlyEntryStartsAtARef` added (+30 lines).
- `src/modules/mc_indi_pos_control/` rewritten in place: McIndiPosControl.{cpp,hpp} = shell copy of MulticopterPositionControl (class/module/event ids renamed, mc_indi_pos_ctrl_*), plus `runIndiStage()` (A2/A3/A5/A6/A7/A8/A13/A14): resetIntegral every cycle, setHoverThrust(ht) with ht = HTE if valid and FLIGHT else MPC_THR_HOVER, never updateHoverThrust; G = g/ht via setThrustModel(G,1); T_meas = mean (omega/omega_max)^2 from esc_status (same code as archive, MC_INDI_W_MAX); jerk FF off; INDI thrust vector t_c/G -> ControlMath::thrustToAttitude; local_pos_sp.thrust = that vector, .acceleration = a_ref. Active only if armed && (pos||vel enabled) && takeoff FLIGHT && !flying_but_ground_contact && attitude/accel fresh (<20 ms) && a_ref finite; else stock attitude setpoint (bypass) and `reset(f_b, collective)` tracking from vehicle_thrust_setpoint (fresh <20 ms) or stock/own last collective. Tilt limit = slewed stock tilt via lib setLimits; collective clamp MPC_THR_MIN/MAX in lib.
- yaml: MC_INDI_POS_EN (renamed from MC_INDIP_EN, default 0), MC_INDI_POS_LPF (10 Hz), MC_INDI_POS_DLY (1). Old external-mode code, MC_INDIP_* params removed.
- CMake: libs GotoControl/PositionControl/Takeoff linked by name via target_link_libraries + include dir (mc_pos_control is configured after this dir, so DEPENDS cannot see them). Kconfig depends on MODULES_MC_POS_CONTROL.
- rc.mc_apps: if/else start pair, old external block removed. `indi_flight/bench/run_scenario.py`: MC_INDIP_EN -> MC_INDI_POS_EN.
- Stock modules: zero diff vs main (checked: git diff main on mc_pos_control, mc_rate_control, mc_att_control, control_allocator, control_allocation, commander is empty).

## Results
- `make px4_sitl_default` (docker): rc 0 after 3 fixes (library target order, include dir, event-id duplicate, float-equal, yaw field).
- Unit tests `make tests 'TESTFILTER=[iI]ndi'`: pass (incl. new test). Break-check: a_c = 0.5*a_ref in accel_only branch -> AccelOnlyEntryStartsAtARef FAILED, rc 2; restored.
- Format: Tools/astyle/check_code_style.sh on module + lib files: no output (clean).
- Flight: see `indi_flight/results/stage5_s60/hover_slice/README.md`. Took off (takeoff_status 1->2 rampup->4->5 flight at 34 s), hovered at 5.0 m for ~60 s, land state 3 at 98 s, z 0.01 m at end, exit ok. Gate PASS (rate RMS 0.0028/0.0028/0.0004 rad/s, pin 0, achieved 1.0).

## UNVERIFIED
- That mc_indi_pos_control (not the fallback mc_pos_control) actually ran: boot param MC_INDI_POS_EN=1 was applied and the binary built, but px4.log has no module start line and the `||` fallback would hide a failed start. Only one publisher of attitude/local-pos setpoint seen (rows equal). Needs `mc_indi_pos_control status` or a log line.
- That the INDI stage was active (not bypass) during the hover: no stage-state field logged (not added). Check by comparing local_pos_sp.thrust vs stock-computed thrust or add a debug topic.
- A8 take-off with ht error -20/0/+20 %, bypass->INDI edge continuity (<2 %), ESC-stale edges, EKF reset behaviour: not tested.
- A4 XY-margin not ported (deferred); tilt limit applied by lib with slewed stock tilt.
- Filter rate taken from work-item dt (1/dt rounded), not the IMU rate; cutoff MC_INDI_POS_LPF vs IMU_ACCEL_CUTOFF match not checked.
- MulticopterPositionControlTest not copied; VTOL arg kept in code but not served by rc scripts.
- Nothing committed.
