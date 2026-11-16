# Decisions

Each entry: decision, alternatives, reason, what would overturn it. Owner decisions (F-, O-) are not re-opened by
the orchestrator; if one looks like the cause of a bad result, ask the owner (`QUESTIONS.md`).

## Owner decisions (from MISSION.md and review section 0, 2026-11-15)

- **F-1 No PID fallback.** INDI runs alone. Robustness is shown by measured margins (G2) and the robustness
  campaign (G3). An oscillation detector that logs and reports is allowed as an instrument only.
- **F-2 Every mode.** The INDI stack serves manual, acro, altitude, position, hold, mission, return, land,
  take-off, offboard and their failsafes. Offboard-only is not the end state.
- **F-3 Generic design, one reference airframe.** Architecture for any quadcopter with eRPM telemetry plus a short,
  justified requirements list. Development and gate evidence on one 5-inch quadcopter of about 600 g, simulated
  from sourced data (stage 1). Other airframes (x500, ~1 kg, >5 kg) flown once at the end as an outlook (G6).
- **F-4 Archive.** `indi_project/` is never modified. Corrections go to `results/errata.md` and the new report.
- **F-5 PID is a reference, never a pass condition.** No gate is a ratio to PID.
- **F-6 The outer loop replaces `mc_pos_control`**, started instead of it by parameter, serving every mode it serves.
- **O-5** Actuator state from measured rotor speed, modelled fallback when telemetry is missing.
- **O-6** Inversion on u = omega^2.
- **O-11** Separate modules behind Kconfig, started from `rc.mc_apps` by parameter; `mc_rate_control`,
  `mc_att_control`, `mc_pos_control`, `control_allocator`, the control-allocation library and commander at zero
  diff against `main`.
- **O-12** Prune bad candidates early, abort bad runs.
- **O-13** A scenario is flown once with the reference controller before it enters a validation set.
- **Identified, never tuned:** physical parameters come from identification.

## Orchestrator decisions

Open, to be written before code (MISSION "Decisions that are yours"):
1. Outer-loop architecture (design project, `design/outer_loop_*`, owner confirmation before stage 5).
2. Steady command/output gap remedy per loop (also absorbs battery sag).
3. Identification concept on an unknown airframe, and behaviour before identification (owner question).
4. Airframe-independent defaults.
5. Yaw from measured rotor acceleration (after the simulator rotor inertia fix).
6. Filter matching at real rates.

### D-1 Reference airframe is a new gz model, not a re-parametrised x500 (2026-11-15)
- Alternatives: scale the x500 SDF parameters in place; use an existing PX4 small-quad model if one fits.
- Reason: every gate result is on this airframe; a separate model with its own sourced values table keeps the
  x500 untouched for the G6 outlook and makes each value traceable.
- Overturn: if an existing PX4 gz model already matches the 5-inch class within 20 % on every value of the table.

### D-2 Reference-airframe model lives in `indi_flight/sim/models/`, served via `PX4_GZ_MODELS` (2026-11-15)
- Alternatives: add it to `Tools/simulation/gz/models` (a submodule: PX4-gazebo-models, a change there is an
  upstream PR to another repo); generate it per run from x500 (the archive's `model_variant.py` approach).
- Reason: no submodule diff, versioned with the evidence, and the runner already overrides `PX4_GZ_MODELS` per run.
  A SITL airframe file (`ROMFS/.../init.d-posix/airframes/4xxx_gz_<name>`) is still needed to start it; it carries
  the `CA_*` geometry and is part of the firmware-side branch only if it is offered upstream (decide at stage 7).
- Overturn: if the overlay path breaks model resolution for nested includes, or upstream later wants the model.

### D-3 Reference-airframe simulation values after the second key (2026-11-15, session 2)
- Values: those of `design/ref_airframe_data.md` with the corrections of `design/ref_airframe_check.md`:
  maxRotVelocity 2700 (14.8 V loaded; battery sag is a later scale on it); rollingMomentCoefficient 5e-8
  (inertia-scaled from x500, keeps the effect at x500 relative size); rotor link izz 5e-5 (= 10 x J_r 5e-6, compensates
  rotorVelocitySlowdownSim 10 so the reaction torque is the physical J_r dw/dt), ixx=iyy 2.5e-5, subtracted from
  base_link; legs and collision box resized to a 5-inch frame; `SIM_GZ_EC_MIN` 0, `THR_MDL_FAC` 1 (exact
  linearisation since w = w_max s), `MPC_THR_HOVER` ~0.13.
- Alternatives: keep x500 rolling moment 1e-6 (20x larger relative disturbance); slowdown 1 (rejected: 446 Hz joint
  speed aliases at a 4 ms physics step); EC_MIN 150 or 600 (idle thrust 36 % of weight at 600, an ESC property the
  INDI loop sees only through telemetry; idle is added later as a plant variant if needed).
- Overturn: a gz run showing the rotor reaction torque does not scale as izz x d(w/10)/dt (sign or size), or J_r
  sources disagreeing by more than 2x once the web re-check is done (J_r is ASSUMED today).

## D-start-fallback (session 12, from review r3 R3-8)
- Decision: `rc.mc_apps` starts `mc_indi_rate_control` / `mc_indi_pos_control` with no `|| mc_*_control start`
  fallback when the INDI parameter is set. If an INDI module fails to start, the vehicle refuses to arm and reports why.
- Alternatives: stock fallback pattern (rejected: a silent PID fallback and a mixed INDI/PID stack, against F-1);
  announced fallback (rejected: F-1 forbids an escape route).
- Overturn: only by the owner (F-1).

## D-G1.6 (session 13): determinism criterion
- Decision: same-seed spread is bounded in absolute terms, against the gate thresholds that consume each metric, and every later verdict must exceed the measured spread (GATES.md G1.6 a-d).
- Alternatives: 2 % relative (rejected: ill-conditioned at the noise floor, 10-25 % on 3 cm deviations); bit-exact replay (needs lockstep between gz and PX4 and wall-clock-free MAVLink sends; out of reach unless T23 shows a cheap cause).
- Overturn: T23 (`design/determinism_s13b.md`) finds a single fixable cause that makes runs bit-identical, or the measured spread exceeds 10 % of a gate threshold.

## D-outer-arch (session 13): architecture A confirmed by the owner (Q1), plus A18 flatness feed-forward
- Decision: A (A1-A17, `design/outer_loop_candidates_r2..r4.md`). Owner asked to consider differential flatness
  (arXiv 1809.04048): A18 = jerk -> omega_ff side channel to the INDI rate module (`design/flatness_r1.md`, F-c).
  It is implemented after base A and kept only if a measured tracking gain exceeds the same-seed spread.
- Alternatives: F-a (no feed-forward), F-b (outer module runs the attitude loop, rejected: mode-dependent rate
  setpoint publishers).
- Overturn: review r5 finds a mode or edge that A18 breaks; tracking test shows no gain.

## D-G1.6-speed (session 14): batch speed factor = 4
- Choice: campaigns run at PX4_SIM_SPEED_FACTOR 4 (~40 s wall per 95 s sim run, one container).
- Alternatives: 1 (2.5x the wall time); 8+ (not tested, gz RTF on this host unknown).
- Reason: 30 same-seed runs (`design/g16_s13.md`): s4 means within the s1 same-seed spread on step and trajectory
  metrics, spreads of the same order.
- Overturned if: INDI runs show a speed-factor effect beyond the same-seed spread (A-4), or the s4 hover outlier
  (max_dev 0.063 m, run r5) turns out to be a speed-factor artefact.

## D-SIM-STEP (session 15): one physics step for every run, 1.25 ms, IMU 800 Hz
- Problem (`design/imu_rate_plan_s15.md`): the runner world has a 4 ms step, so the IMU (and the rate loop) cannot
  exceed 250 Hz; G2 needs 400 and 800 Hz. `run_scenario.py:182-186` sets the step to 1/imu_rate (breaks the rule
  "variants do not change the physics step with the IMU rate"). PX4 decimates the gyro by round(sensor/RATEMAX).
- Choice: a fixed 1.25 ms step (800 Hz) world for all runs, IMU 800 Hz. 800 Hz and 400 Hz are exact (decimation 1, 2).
  The G2 "250 Hz reported" point runs at 800/3 = 267 Hz and is labelled so. The runner's step/IMU coupling is removed.
- Alternatives: 1 ms step, IMU 1 kHz (250 exact, 400 -> 333 Hz, 800 -> 1 kHz: the two pass rates not exact,
  rejected); 0.25 ms step, IMU 4 kHz (all exact, 5x physics and 5x IMU messages at speed 4, CPU unmeasured: kept as
  the fallback); per-rate step (rejected, rule).
- Consequence: 4 ms-step results (G1.6 set, PID references) are not comparable with later runs; the PID baseline and a
  short G1.6 repeat (5 runs x 3 scenarios, speed 4) are re-flown on the new world. Cycle-count parameters
  (MC_INDI_DELAY, MC_INDI_ERPM_DLY, MC_INDI_DT_MAX) are converted to time or scaled per rate in stage 3.
- Overturned if: the 1.25 ms world does not reach speed factor 4 on this host, or a pre-test shows a step-size effect on
  the plant (rotor dynamics, contact) beyond the same-seed spread; then measure the 0.25 ms option.

## D-SCHED (session 23): G1.6(a) remedy = sim-time scenario player inside PX4 (sim-only module)
- Problem: G1.6(a) NOT MET (mode-instant spread 7.5-11 ms vs 2.5 ms); cause known (G1.6 c): arm, mode commands and
  the offboard setpoint stream go over MAVLink/UDP from the runner, so each lands on a different IMU tick. The same
  path also carries G1.5 injections (applied time must be within one physics step of the commanded sim time) and
  will carry G5 events (mode switches in motion, RC/data-link loss, kill, false maybe_landed).
- Choice: a sim-only PX4 module (`src/modules/simulation/`, own Kconfig, SITL only, not in the upstream firmware
  branch) that plays a schedule file written by the runner: rows `t_sim_us, kind, fields` for arm/disarm and mode
  (vehicle_command on uORB, commander unchanged), offboard_control_mode + trajectory_setpoint, manual_control_setpoint
  (stick modes), parameter steps, and injector triggers. It runs on the gyro callback and publishes the row on the
  first tick with hrt >= t_sim; each applied row is logged (new sim topic) with its applied time. The runner keeps
  MAVLink only for start-up checks and as a fallback for archived scenarios.
- Alternatives: (1) lockstep gz with PX4 (gz waits for actuator outputs): makes runs closer to bit-exact but touches
  the gz/PX4 timing contract of every run and does not fix the wall-clock MAVLink sends; kept as a later option if
  (b) spreads stay above 10 % of a threshold. (2) Restate G1.6(a) as "window anchored on the logged mode change":
  rejected for now, it weakens the test and leaves G1.5 applied-time unmet anyway. (3) Mode switch only, setpoints
  still over MAVLink: rejected, the 50 Hz setpoint stream has the same jitter and G5 needs stick inputs in sim time.
- Cost estimate: one sonnet implementation session (module + runner writer + 1 pre-test), one second-key session.
- Overturn: the player cannot be built in two sessions, or with it the mode-instant spread is still > 2 IMU periods
  (then the residual comes from gz/PX4 timing, and lockstep is next).
- Outcome S24: built in one session (b2dab14759); 2 hovers gave 0 us spread on arm and offboard instants (second key
  agrees). hrt is the gz clock in SITL (lockstep scheduler). Commander adds a fixed 6.25/16.25 ms after the applied row.

## D-A17 Commander loop phase: start gz paused, unpause after PX4 start-up (S25, 2026-11-16)
- Problem: A-17. Commander (zero diff, O-11) runs a 10 ms sleep loop whose phase is set when it starts. gz is
  started running (`gz sim -r`), so PX4 modules start while the sim clock already advances: the phase is a
  wall-clock race (2500/3750/6250 us over 5 runs). G1.6(a) asks mode instants within 2.5 ms across runs.
- Choice: the runner starts gz paused (no `-r`), waits until PX4 start-up is complete (all modules started in
  frozen sim time), then unpauses through the world control service. Every module then begins its loop at the
  same sim time in every run. Sim and runner only; no firmware diff.
- Alternatives: (1) player waits for a Commander publish before a mode row: moves the trigger, not the response,
  so instants still differ in absolute sim time; (2) restate G1.6(a) relative to a phase-aligned scenario origin:
  a test change after first test (owner question), kept as fallback; (3) lockstep gz: larger change, not needed
  for this cause.
- Overturn: PX4 start-up blocks while time is frozen (rcS sleeps are px4_usleep in lockstep) and no unpause
  point exists after commander start; or with it the phase still differs across runs.
- Outcome S25 (T52, `results/a17_paused_s25/README.md`): start-up completes in frozen sim time and all modules
  start at t=0, yet the arm/offboard spread is 8.75/6.25 ms over 5 runs and r3 shifts phase within the run.
  Overturned. Cause from source: `Commander.cpp` skips its 10 ms `px4_usleep` while a vehicle_command is pending and
  sleeps relative to the end of variable work; gz runs free (not lockstepped), so that wall time becomes a random
  sim-time shift in 1.25 ms steps. Only lockstep gz removes it. A-17 parked (2-session rule), owner Q3.

## D-A14 Sim baro consistent with the world altitude (S28, 2026-11-16)
- Problem: A-14. The gz `air_pressure` sensor of `quad5in_base` uses reference altitude 0, so it reads sea-level
  pressure while `default.sdf` puts the origin at 488 m. PX4's on-ground baro/GNSS autocal (`SENS_BAR_AUTOCAL`,
  `VehicleAirData.cpp:273`) steps the baro by ~488 m after EKF2 started fusing it; the EKF2 baro-bias estimate is
  still converging at arm, and the gate accepts the residual in some same-seed runs (EKF z 2.3 m off, hold 7.2 m).
- Choice: `<reference_altitude>488</reference_altitude>` in the model's air_pressure sensor (sim only, no firmware
  diff). The raw baro then agrees with GNSS from boot, autocal changes almost nothing, the bias starts near its value.
- Alternatives: (1) `EKF2_BARO_CTRL 0` on the bench: removes the baro from every test, so baro-related failsafes and
  estimator resets of G5 would not be exercised; kept as fallback. (2) Player arms only when |z_est - z_truth|
  < 0.1 m: bounds the symptom, keeps the 488 m transient in every run. (3) `SENS_BAR_AUTOCAL 0`: the baro keeps a
  488 m offset to GNSS, a configuration no real vehicle has.
- Coupling: the value must equal the world elevation; a different world needs its own value (stated in the SDF).
- Overturn: the closing test (`bench/a14_close.sh`, 15 same-seed hovers speed 4) shows raw pressure not ~95600 Pa,
  a baro fault, EKF z error >= 0.1 m in 15-35 s or hold spread >= 0.05 m; then take alternative (1).
