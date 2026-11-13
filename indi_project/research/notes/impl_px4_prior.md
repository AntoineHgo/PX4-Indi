# Prior attempts to implement INDI in PX4 (research note)

Sources: local copies under `indi_project/research/raw/` only (no downloads).
Status: complete (all items read).

## 1. PR #25216 - "[WIP] Implement INDI control law with supporting infrastructure"
- URL: https://github.com/PX4/PX4-Autopilot/pull/25216
- Author: rohan908 (author_association NONE). Created 2025-07-14, last commit 2025-07-21.
- State: CLOSED, not merged. Closed by github-actions stale bot (label `stale`): warned 2025-12-12, auto-closed 2026-01-13 after 120 days, then closed again 2026-05-30 (so it was reopened in between). 34 commits, +1517/-1, 16 files.
- Scope: new module `src/modules/mc_indi_rate_control/` (MulticopterINDIRateControl.cpp/hpp, ActuatorEffectivenessRotorsINDI.cpp/hpp, params, module.yaml, Kconfig). Also touches `ROMFS/.../rc.mc_apps` (conditional start), `commander` (enable/disable INDI), `mc_rate_control` integration, `control_allocator` (author says "crucial errors ... non-metric effectiveness matrix in the control allocator"), `VehicleTorqueSetpoint.msg`, new `IndiAdaptationStatus.msg`, `logged_topics.cpp`, SITL x500 airframe `4001_gz_x500`.
- Layer: INDI sits in the RATE loop, on top of the existing PID rate controller. Final torque published as `xyz = pid_xyz + indi_torque_xyz` (diff ~L1030). Torque space, mapped to actuators via a rotor effectiveness matrix G1 (moment part, applied to w^2) and G2 (gyroscopic part, applied to dw/dt). Allocation: the module builds its own G1/G2 from metric rotor parameters. The diff still modifies `ControlAllocator`, and rohan908 said the `CA_*` parameters are not metric. Jaeyoung-Lim said CA should not run during iNDI. Whether the final branch bypasses CA is unclear.
- Actuator state: from ESC RPM (`esc_status.esc[i].esc_rpm` -> rad/s), passed through a `LowPassFilter2p` per rotor (cutoff = IMU gyro cutoff param) and differentiated for dw/dt. Not a model.
- Angular acceleration: `vehicle_angular_velocity.xyz_derivative`, not filtered further (diff ~L1000).
- Measured torque: `measured_body_torque = _Iv * angular_accel` published for comparison (debug only).
- Yaw output additionally low-passed (`AlphaFilter`, `MC_YAW_TQ` cutoff).
- Filter matching: not an explicit match. The INDI term uses the same rate-loop timestamp dt (clamped 0.125 ms to 20 ms). The rotor-speed filter and angular-accel path use separate dt computations; no explicit phase-matching of the rotor-speed and gyro-derivative filters was seen.
- Parameters added (diff): `MC_INDI_EN` (default 1), `MC_INDI_ADAPT_EN` (default 0), `INDI_ADAPT_R/P/Y` (default 1.5, per-axis adaptation), per-rotor `MET_ROTOR${i}_CT`, `MET_ROTOR${i}_KM`, `MET_ROTOR${i}_IZZ` (metric geometry, duplicating `CA_*` values), `INDI_G1_ADAPT_${i}`, `INDI_G2_ADAPT_${i}`.
- uORB: uses `esc_status`, `vehicle_angular_velocity`, `vehicle_rates_setpoint`, `vehicle_control_mode`, `vehicle_land_detected`, `battery_status`, `control_allocator_status`, `parameter_update`. Publishes `vehicle_torque_setpoint` (extended with `pid_xyz`, `indi_torque_xyz`, `g1_term`, `g2_term`, `measured_body_torque_xyz`), `vehicle_thrust_setpoint`, `rate_ctrl_status`, `actuator_controls_status_0`, and new `indi_adaptation_status` (rotor speeds, G1/G2 flattened 3x16, adaptive constants, published at 100 Hz when adaptation is on).
- Adaptation: online adapt of G1/G2 scalars from `delta_radps` and `delta_angular_accel` (off by default).

### Reviewer / maintainer comments (quoted, abbreviated)
- Jaeyoung-Lim (2025-07-14, CHANGES_REQUESTED): "I would rather separate this out as a separate module (e.g. `mc_indi_rate_control`) so that you are less tangled with the rest of the system (such as commander) and it is less safety critical by modifying the existing rate controller." Also: "On the allocation side, we can now use the control allocator as a library. My suggestion would be to do the allocation inside the new module, without touching the control allocator."
- Jaeyoung-Lim (review comment): "I would not enable/disable indi control in commander. Rather, I would just start the module to replace the mc_rate_controller in the rcS."
- Jaeyoung-Lim: "Unless this is tested with VTOL, lets remove all the implementation regarding vtol handling." Also asked "Does the indi not track linear acceleration?" (answer given: body torque only).
- Jaeyoung-Lim: "This seems a bit strange. So you are incrementing on top of the rate controller output, rather than incrementing against the previous torque setpoint?"
- Jaeyoung-Lim (2025-07-24, on the 'desired minus measured' argument): "The desired angular acceleration is substracted by the filtered angular acceleration measured from the gyro. The filtered angular acceleration is NOT the same as the output of the unmodified rate controller, unless the torque is perfectly being tracked. The reason iNDI controller is robust is because it uses measurements to correct it's commands."
- Jaeyoung-Lim (2025-07-24): "@rohan908 Why do you care about the control_allocator module? IMO, you should not run it when doing iNDI."
- Jaeyoung-Lim (2025-07-23): "What is the downside of just using Ct and Km in CA_ and use them as metric parameters? Defining additonal parameters will use a lot of flash space." Also on logging: "These would be quite expensive to log at a high rate."
- Pedro-Roque (2025-07-23): "measured_torque shouldn't belong in a torque setpoint message." Also "I'd use those parameters [CA_]and specify to the user that these should be metric." Then: "I still would like to check what exactly fails in ControlAllocator if you use those variables as metric."
- dagar (2025-07-14): asked for it as "an optional alternate rate controller (eg mc_indi_rate_control) so that there's no potential cost or downside to regular users." Author replied it "forces this to be a seperate module".
- hamishwillee: uORB message documentation style fixes (units in brackets, single-space comments) on `IndiAdaptationStatus.msg`; docs standard pointed to the uORB documentation page (2026-01-29).
- Reviews by Jaeyoung-Lim, Pedro-Roque; no approval recorded. Closed by stale bot, not by a maintainer decision.

### Test / flight results
- No flight or SITL result numbers in the PR body. Body only says: "To know if it is working the `indi_torque_setpoint` should follow the `measured_torque` closely" (plotjuggler check). Rotor geometry was calibrated for x500 (commit "Corrected and caluclated all inertial and constants for x500 drone!", 2025-06-23). No success claims in comments.
- Author states it was implemented from Sihao Sun's comparative study and an adaptive-INDI TU Delft paper (author names of that paper not checked).

## 2. PR #25166 - "[WIP] 3D acceleration control using iNDI for Fixed-wings" (fixed-wing, multicopter relevance low)
- URL: https://github.com/PX4/PX4-Autopilot/pull/25166
- Author: Jaeyoung-Lim (PX4 core maintainer; body credits a master's thesis by @MarvinHarms). Created 2025-07-07. Draft flag: true.
- State: API says OPEN. But the bot posted "automatically closed due to 120 days of inactivity" on 2026-01-11 and again 2026-08-13, so the PR was closed and reopened or the state is stale. Treat as open/stalled. Labels: `status:stale`, `vehicle:fixed-wing`, `kind:test`.
- Scope: 12 files, +1271/-0. New `src/lib/fw_indi_control/` (FixedWingIndiControl: `get_flat_attitude(vel, f)` computes an attitude from the desired force vector projected on lift/drag axes, uses wind estimate, air density from calibrated airspeed, C_L coefficients) and `src/modules/fw_indi_pos_control/` (FixedwingIndiPosControl, params `FW_INDI_MASS`, `FW_INDI_KP_X/Y/Z`, `FW_INDI_KV_X/Y/Z`, `FW_INDI_K_ROLL`). Board/ROMFS: `rc.fw_apps`, sitl default.px4board.
- Layer: OUTER loop. Acceleration reference is turned into rate/attitude setpoints: publishes `vehicle_rates_setpoint`, `vehicle_attitude_setpoint`, `offboard_control_mode`. It is an acceleration/position-level iNDI, not a rate-loop INDI. Not torque space; no actuator model.
- Actuator state: none used (no ESC RPM). Uses `vehicle_angular_velocity`, `vehicle_acceleration`, `vehicle_attitude`, `vehicle_local_position`, `airspeed_validated`, `trajectory_setpoint`, `control_allocator_status` (multi-array).
- Filters: none described in the visible diff.
- Body text (author): "Current PX4 control is done model-free ... this can result in sub-optimal performance ... This implementation comes from Master's thesis of @MarvinHarms ... generates vehicle body rates setpoints from the acceleration input using the vehicle's aerodynamic coefficients. The current implementation uses offboard mode to interact with the rest of the stack."
- Comments: only bot messages (stale, auto-close, title and commit-message lint: "WIP commit should not be merged", FLASH size analysis for px4_fmu-v5x: +16 byte). No maintainer design review text found in `pr_25166_comments.json`. `pr_25166_rc.json` not read (not needed for the brief).
- Test/flight results: none reported in the body; "Test coverage" section left as template. A gtest `fw_indi_control_test.cpp` exists (unit test of get_flat_attitude only).
- Relevance for multicopter: the attitude/acceleration-level structure and the "robust to model" framing are useful; the code itself is fixed-wing specific.

## 3. PR #25863 and #25864 - "Pr indi accel" / "Indi accel" (both by Wing57)
- URLs: https://github.com/PX4/PX4-Autopilot/pull/25863 and https://github.com/PX4/PX4-Autopilot/pull/25864
- Author: Wing57. Created 2025-11-03. #25863 closed 2025-11-03 19:38 (3 min after opening); #25864 closed 2025-11-03 20:24 (about 14 min after opening). Both closed, not merged.
- Body (one line each): #25863 "Using NMPC paper equation for desired angular accel with current INDI framework"; #25864 "Implementation of NMPC desired angular accel equation into existing INDI framework". Both show 16 files, +1647/-1 (same stats). No comments, no labels, no closer exposed by the API.
- Implementation: the body describes an NMPC-derived desired angular acceleration fed into an existing INDI framework (rate-loop reference). The diff is not in the raw data, so the code was not read. The 'current INDI framework' is not in PX4 main, so it lives in a fork or branch we do not have.
- Conclusion: no outcome or review data. Closure reason is not stated; the 3- and 14-minute gaps between open and close suggest a superseded or mistaken submission (guess). Do not cite as evidence of a technical failure.

## 4. Forum threads (no code merged; community attempts)
- Thread A: https://discuss.px4.io/t/10953 (id 10953, "Dynamic Inversion for Multicopters"). Opened 2019-05-10 by toopazo (Penn State VLCOE). 9 posts. Plan: NDI/INDI for multicopters, 30-40 gains, outer loop velocity->angles, inner loop angles->throttle. bresch (2019-05-15) asked whether NDI would be an angular-rate controller; Jaeyoung-Lim (2019-05-14): "it would make more appropriate to implement it on ROS as a offboard controller". bresch: "relying on an offboard communication in order to simply stabilize the drone is way too dangerous." Jaeyoung-Lim later: offboard rate setpoints work, but "never use offboard" for an NDI rate loop (his reply to bresch). Last post 2024-01-31 asks for news; no outcome.
- Thread B: https://discuss.px4.io/t/indi-controller-on-px4/36293 (id 36293, "INDI Controller on PX4"). Opened 2024-01-15 by Romain13004. 17 posts. Asked how to port lei-ss/indi (PX4 2016, QGC fork needed). JulianOes (PX4 dev) asked at which loop level it fits (rate, attitude, velocity, position).
  - lviron (2024-02-28): transplanted into PX4 SITL/Gazebo; drone "could not take off and just kept shaking". Got G1 from a Gazebo log under PID control; computed actuator state from ESC RPM and angular acceleration as increment. (2024-03-05): takes off but shakes; motor speed oscillates between stall and max. Cutoffs: 8 Hz on motor RPM vs 20 Hz on rates; "If same, the vehicle can not take off." Ignored G2.
  - l528045193 (2024-03-01/07): implemented INDI in `rate_control.cpp` at 800 Hz, works in Gazebo, "strong jitter on the real F450 rack". Later: 250 Hz in Gazebo; rate PD P 6.8 D 10; G1 P 0.26, Q 0.20, R 0.095; G2 set to 1.05 (said "G2 can be ignored first and has little impact"); output and angular-accel filters both 8 Hz low-pass. Said the real drone did not need parameter changes while Gazebo behaved differently (his words: "strange").
  - wuwenhao78 (2024-05) and liujia_72 (2026-10) asked for code by private email; Pol_De_Petris (2025-09) asked for status. No public repo or patch posted in the thread.
  - yigitcan-ozturk (2026-10-27) asked for a reproducible implementation with: PX4 version and modifications, how angular acceleration is estimated and filtered, how INDI effectiveness is determined, filter delay vs controller rate, actuator saturation/allocation handling, and SITL logs of commanded vs measured rates, estimated angular accel and actuator outputs. No reply in the file.
- Test/flight results in forum: qualitative only (SITL takes off or not; real jitter; shaking). No logs or plots in text; bokeh plots referenced but not in raw data.

## 5. GitHub issue search results (issues_*.json)
- Four search files (`angular_acceleration_feedback`, `incremental_dynamic_inversion`, `incremental_nonlinear_dynamic_inversion`, `INDI`) return mostly unrelated hits (e.g. #11070, #14505, #21504, #18413 menuconfig). Only #25166, #25216, #25863, #25864 are INDI-related. #25966 (3D wind estimator, fixed-wing, open) does not mention INDI. #20237, #20080, #24120 (fixed-wing rate control, Jaeyoung-Lim) are the related fixed-wing rate-control infrastructure, not INDI.
- No separate GitHub issue about INDI was found in this data.

## 6. lei-ss/indi (Paparazzi INDI port, master branch read)
- URL: https://github.com/lei-ss/indi (description "use paparazzi indi attitude controler (simple) in px4 firmware"). Created 2017-08-01, last push 2018-05-28. 24 stars, 1 open issue. Default branch master; README says `att_indi` is the main code branch (not read). Targets a 2016 PX4 with `multirotor_motor_limits`, `control_state`, `mc_att_ctrl_status` topics (removed in current PX4) and a QGC fork.
- Files read: `mc_att_control_indi/mc_att_control_indi_main.cpp` (1977 lines; core functions at ~L949-1220 and `control_attitude`/`control_attitude_rates` ~L1249-1620), `stabilization_indi.h`. Defaults in `airframe.h`. `mc_att_control_indi_params.c` not read.
- Layer: attitude loop reference (`stabilization_indi_run`, reference model with err/rate gains 100/14) plus a rate-control override (`rate_control` true uses `vehicle_rates_setpoint` directly, ~L1122). INDI works on angular acceleration per axis (roll/pitch/yaw). Output is `attitude commands / 4500`, i.e. a per-axis normalized actuator command, not per motor.
- Torque/actuator space: no explicit torque; increment `du = (1/G1) * (ang_accel_ref - rate_d)` with G1 a per-axis scalar (`airframe.h`: G1 P 0.034799, Q 0.011948, R 0.004186; G2 R 0.000001). Yaw adds G2 term. So it is a per-axis scalar INDI (Paparazzi simple form), not a full G-matrix allocation.
- Increment form: `u_in = u_filtered_prev + du` (incremental on the previous filtered command, not PID+INDI). Bounded to +-4500. Increment frozen below `MIN_TAKEOFF_THRUST` and clamped by `multirotor_motor_limits` saturation flags (~L1137-1170).
- Actuator state: a first-order model of actuator dynamics on the commanded input (`ACT_DYN_P/Q/R` = 0.1, ~L1190). No ESC RPM in master; README: "tested with dji450 frame without rotor rpm feedback".
- Filters: 2nd-order Butterworth on both gyro rates and the command history, same cutoff per axis (`FILT_CUTOFF` 3.2 Hz in airframe.h; macro default 8 Hz; yaw separate `FILT_CUTOFF_R`). Angular acceleration is a finite difference of the filtered rate. Filter matching is by identical cutoff, not by delay compensation.
- Adaptation: `lms_estimation` adapts G1 and G2 online (mu = 0.0001), off by default (`STABILIZATION_INDI_USE_ADAPTIVE FALSE`), clamps G >= 0.01.
- Real flight data: README only ("flight performance is not bad" on DJI F450 without RPM feedback). No logs.

## Lessons for our design (interpretation, not from the sources)
1. Ship as a separate, parameter-selected rate controller module (the way dagar and Jaeyoung-Lim asked). Do not touch commander, `mc_rate_control` or `ControlAllocator` in the first PR; both review threads treated those edits as the main blocker.
2. Use the incremental form on the previous actuator command (`u = u_prev + G^-1 (a_ref - a_meas_filtered)`), as lei-ss does. PR 25216 used `xyz = pid + indi`, with an INDI term that was the full estimated torque `G1*w^2 + G2*dw/dt`, not an increment. Jaeyoung-Lim flagged it as "strange" and not robust.
3. Match filter delay between the measured angular acceleration and the actuator-state signal (same cutoff, same group delay). The takeoff failures in the forum match cutoff mismatch (8 Hz RPM vs 20 Hz rates) and 800 Hz vs 250 Hz loop mismatch.
4. Decide the actuator-state source up front: ESC RPM (`esc_status`, PR 25216) or a first-order command model (lei-ss). Make the other one a fallback. Do not assume RPM telemetry exists on every ESC.
5. Use the existing `CA_*` geometry (metric) instead of duplicate `MET_*` parameters, which reviewers rejected for flash cost; log INDI internals at low rate and default off (IndiAdaptationStatus at 100 Hz was rejected).
6. Gate the increment on thrust and motor saturation from day one (lei-ss does this; forum failures happened on takeoff).
7. Define the validation before coding: SITL and log plots of commanded vs measured rate, estimated angular acceleration and actuator output, as yigitcan-ozturk asked. None of the PRs reported numbers, so there is no baseline to compare against.
8. Keep PRs small and reviewable. PR 25216 (+1517 lines, 34 commits) got CHANGES_REQUESTED from Jaeyoung-Lim (twice) and Pedro-Roque, and was closed by the stale bot. PR 25166 is a draft that is still stalled.

## Unverified / unclear
- PR 25216 final state: whether ControlAllocator was bypassed, whether the `pid + indi` torque combination was changed later, and any commits after 2025-07-21 (not checked).
- PR 25166 is listed as OPEN by the API, but the bot posted auto-close comments dated 2026-01-11 and 2026-08-13. Whether it was reopened is unclear.
- PR 25863 and 25864: code and closing reason unknown. No diff in the raw data.
- lei-ss: only `master` read. `att_indi` (the README's main branch) and `mc_att_control_indi_params.c` not read. Whether the PX4 port was ever run on hardware with the posted numbers is unknown.
- Forum thread B: whether lviron and l528045193 resolved their takeoff and jitter problems; whether l528045193's 800 Hz code was shared. The G1 values differ widely (0.26 in forum vs 0.035 in lei-ss `airframe.h`), so they are not comparable without the scaling.
- Forum thread A (2019): no outcome in the data.
- bresch's role at PX4 is not stated in the data.
- The TU Delft paper author names (Smeur et al.) are my recollection, not checked against the PR.
- No maintainer ruled on INDI design in writing. The PR 25216 closure was automatic (stale bot), not a design decision.
