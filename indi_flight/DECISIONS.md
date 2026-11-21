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
- Outcome S28 pretest (`results/a14_close_s28/pretest_check.md`): raw pressure unchanged (101324 Pa), bias -488 ->
  baro fault: the edit did not reach the simulated sensor. Not yet overturned: check model load path first.

## D-EFFORT-BW Motor effort metric at a fixed bandwidth (S29, 2026-11-16)
- Context: `motor_rate_rms_per_s` was a raw first difference at the logged rate (defect 2 of
  `design/g13_g14_matrix_s28.md`, A-11): its value moves with the log rate and with noise above any motor response.
- Choice: `actuator_motors` resampled on a uniform 400 Hz sim-time grid, zero-phase 2nd-order Butterworth low-pass
  at 50 Hz, RMS of the derivative per motor and mean. 400 Hz is the lowest G2 controller rate whose Nyquist (200 Hz)
  still leaves the filter a decade of roll-off; 50 Hz is about ten times the reference motor bandwidth (tau ~30 ms,
  ~5 Hz), so the metric keeps every command change the rotor can follow plus the band where ESC heating and audible
  ripple come from, and drops sensor noise the motor cannot reproduce. The raw value is kept for errata.
- Alternatives: (1) raw derivative at a fixed log rate: still noise-dominated; (2) filter at the motor bandwidth
  (~5 Hz): hides command chatter that heats ESCs; (3) true rotor-speed ripple only: kept for G4 as a separate limit.
- Overturn: G4 sources (stage 1 noise profiles) show command content above 50 Hz that matters on a vehicle, or the
  250 Hz controller rate must be scored with the same metric (then 250 Hz grid, 50 Hz cut still below Nyquist).
- S29 (T60, `design/a14_refalt_s29.md`): SDF choice OVERTURNED. gz-sensors 8 `AirPressureSensor::Load` never reads
  `reference_altitude` (set only by `SetReferenceAltitude()`, which gz-sim 8 `Sensors.cc` never calls); pressure is
  ISA at `0 + pose.z`, world elevation unused. New choice: in the sim-only `gz_bridge` (already modified on this
  branch, not an O-11 zero-diff module), re-express the gz pressure at the world origin altitude (ISA altitude of
  the gz value + world elevation from the spherical coordinates -> ISA pressure), two keys (simulator hook). Fallback
  unchanged: alternative (1) `EKF2_BARO_CTRL 0`. Closing test unchanged (`bench/a14_close.sh` minus the SDF swap).

## D-RATE267 (S35): G2 "250 Hz reported" is flown at 266.7 Hz
- Choice: the third controller rate of G2 (reported only, not a pass condition) is 266.7 Hz = 3 physics steps of
  1.25 ms (D-SIM-STEP), the rate `bench/run_scenario.py:37` already offers.
- Alternatives: 250 Hz exactly (4 ms = 3.2 physics steps: the controller period would jitter between 3 and 4 steps,
  adding a non-physical delay variation to a margin measurement); a 1 ms physics step (changes every G1.6 result).
- Overturn if: a reviewer or the owner needs the exact 250 Hz figure, or the physics step changes.

## D-G2-BREAK (S36): INDI rate-loop margins are measured at the torque-setpoint break
- Choice: for INDI the primary G2 rate-loop break is M3a in `mc_indi_rate_control` (our module, O-11 allows it):
  a bench-only injection d added to the controller's torque output c, with u = c + d sent to BOTH the publish and
  the stored previous torque setpoint (`McIndiRateControl.cpp:329` and `:331`), so every feedback path (gyro, measured
  rotor speed, modelled actuator) closes through u. L = -G_cd/G_ud. The gyro break (M1) is kept for INDI as a
  secondary result, reported as the gyro-path gain L_o/(1+L_i), not as the loop gain. PID keeps M1 (gyro) as
  primary and M2 as cross-check (its loop has a single feedback path; `mc_rate_control` stays at zero diff).
- Alternatives: M1 for both stacks (review r1 finding 1: misses the model and rotor-speed paths of INDI, so its
  margins are not the loop's); M2 actuator break (leaves the model path closed); injecting in the allocator
  (breaks the zero-diff rule).
- Overturn if: the M3a injection changes the controller's behaviour with d = 0 (bit-identical check on one flight),
  or M3a and the linear model of section 4.1 disagree by more than the G2 tolerance with no explained cause.

## D-G2-INJ (S39): M3a excitation is generated inside `mc_indi_rate_control`, bench parameters, off by default
- Choice: parameters `MC_INDI_INJ_AX` (0 off, 1 roll, 2 pitch, 3 yaw), `MC_INDI_INJ_AMP` (normalised torque per
  sine component), `MC_INDI_INJ_TP` (period s), `MC_INDI_INJ_FMIN/FMAX`, `MC_INDI_INJ_NP` (number of periods).
  The module generates a Schroeder-phase multisine on the 1/Tp grid with the bin selection of
  `bench/margins_est.py:log_bins` (10 per decade), clock = the module's cycle timestamp (sim time in SITL), origin =
  first cycle with the axis set, airborne and armed; d = 0 outside [0, NP*Tp] and whenever landed (r2: c does not
  depend on u while landed). u = c + d goes to both the publish and the stored previous setpoint (D-G2-BREAK).
  c, d and u are logged in `indi_rate_status` (new fields, one sample per cycle); `indi_rate_status` and
  `actuator_torque_measured` are logged at interval 0. With AX = 0 the code path adds exact zero (d is not computed).
- Alternatives: injection from gz_bridge into the torque topic (would have to sit between module and allocator, a
  second publisher of `vehicle_torque_setpoint`, racy, and does not reach the stored setpoint); the stock
  `mc_autotune_attitude_control` signal (injects on the rate setpoint, i.e. M-type outer break, not M3a, and its
  signal is not periodic on a fixed grid); a Kconfig compile guard (adds a build variant; deferred to G7, where the
  firmware-only PR branch either keeps it as a documented system-identification feature or removes it).
- Overturn if: AX = 0 changes any logged output against the previous build on the unit tests, or the G7 review
  finds a bench feature unacceptable upstream (then a Kconfig option, default n, enabled in SITL only).

## D-G1-DERIVE (S45): rate-loop G1 is derived from airframe data, never regressed from a closed-loop log (provisional, part of decisions 3 and 4)
- Choice: G1_R/P/Y are computed from the allocator's normalisation and physical data: roll/pitch
  G1 = sum_i |p_i| T_max,i / (sqrt(2) I) with T_max = m g / (n x_hover) (`results/stage2_s44/a22_links.md` closed form),
  yaw G1 = n km T_max / Izz (`results/stage2_s45/g1y_derivation.md`). Inputs: CA_ROTORn_* geometry and KM, mass,
  inertia, hover thrust fraction from a non-saturated hover. Until identification (decision 3) exists, the bench
  sets the derived values for quad5in (1756 / 1599 / 215) on every INDI flight; the firmware defaults (320/210/30)
  are not a validated configuration and must change before G6.
- Alternatives: regression of alpha on u from a flight (S42/S43: returns the delivered fraction under saturation,
  0.19x the plant, and drove A-23); online adaptive estimate (deferred to decision 3, needs a saturation gate:
  `torque_setpoint_achieved`, motor pin fraction); tuning (forbidden, lesson 8).
- Evidence: S44 derived R/P removed the rate oscillation (32x); S45 derived Y removed motor pinning (46 % -> 0 %),
  second key AGREE.
- Overturn if: a small-signal regression on a clean (unsaturated) hover differs from the derived value by > 15 %
  on any axis, or the stage-4 identification gives a different value with an explained cause.
- Update S46 (two keys): inertia is the TOTAL about the CoG (base_link + 4 rotor links with parallel-axis terms):
  Ixx/Iyy/Izz 1.400e-3/1.500e-3/2.700e-3; S45 had scaled Iyy by the base_link ratio (1.533e-3, G1_P 2.3 % low). Bench
  values now 1757 / 1640 / 205 (`bench/params/quad5in_indi_g1.params`, `results/stage2_s46/`). Yaw counts the rotors' own
  spin Izz because gz prescribes rotor joint speed relative to the body (222 without it, 7 % apart, within the G3 G1 range);
  a yaw step identification in stage 4 settles it.

## D-G2Y-DERIVE (S47): yaw spin-up term G2_Y derived from rotor inertia, not left at 0
- Choice: MC_INDI_G2_Y = G1_Y * J_r / (2 k_m w_h), with J_r the rotor spin inertia that reacts on the body, k_m the
  yaw torque constant (momentConstant x motorConstant) and w_h the hover rotor speed. quad5in: J_r 5e-6 (gz slowdown 10),
  k_m 1.9e-8, w_h 999 -> tau 0.132 s, G2_Y 27 (bench params). This is decision 5 of the mission, taken early because
  G2_Y 0 left a bistable 41 Hz yaw limit cycle (A-25) once G1_Y had its true value.
- Alternatives: G2 0 with a lower yaw bandwidth (rejected: the plant has the spin-up term whatever the bandwidth, and
  the loop gain at 41 Hz is ~34x the model's); G2 from measured rotor acceleration only (stage 3 option, same number at
  hover); G2 scheduled with measured w (G2 ~ 1/w; stage 3 decides).
- The firmware parameter description ("about G1_Y x loop period, 0.02") is wrong for this airframe; fix in stage 3.
- Overturn if: a yaw step or injection identification gives G2 more than 30 % away with an explained cause, or the
  second key (`results/stage2_s47/g2_second_key.md`) disagrees.

## D-RATE-LEAD (S48, PROPOSED for stage 3, not implemented): rate-prediction lead in the INDI rate law
- Finding (`results/stage2_s48/README.md`): with matched INDI the loop at the torque break is ~ K A(s)(1+P_att/s)/s; the
  motor lag (tau 33 ms) caps K_R near 20 rad/s and, with MC_ROLL_P 8 (stock cascade), PM is 29 deg; G2 is unreachable by
  gains alone (needs P_att <= 2.5). Model matches the S47 measurement within 1.3 deg PM / 0.6 dB GM.
- Choice proposed: nu = K (rate_sp - w) - K tau_c a_f with tau_c = MC_INDI_ACT_TC (identified), i.e. rate prediction one
  actuator time constant ahead, cancelling the actuator pole: model PM 56-61 deg, GM 11-16 dB at K 20-40, 800 Hz, P_att 8.
- Alternatives: (a) lower MC_ROLL_P for INDI airframes (slow attitude loop, ~0.4 Hz, rejected for F-2 manual/acro feel);
  (b) higher K_R (worse, see sweep); (c) full actuator-dynamics inversion in the reference model (more parameters);
  (d) leave as is and fail G2 (no).
- Open before code: two keys on the model (T101), flight check that the model predicts parameter changes (m3a_check),
  noise cost on motor command (G4), interaction with the measured-rotor-speed path and the blend, yaw axis with G2_Y.
- Overturn if: the flight check disagrees with the model by > 10 deg PM, or the lead's motor-command noise exceeds the G4
  limit at the K that meets G2.
- S49: design note drafted (`design/rate_lead_note.md`, new param MC_INDI_LEAD 0..1). Delay-calibrated model sweep
  (`results/stage2_s49/lead_delay_README.md`, unkeyed): K20 400 Hz PM 57/GM 10.5 dB; K40 fails. Default K_R stays 20.
  Also overturn if: the measured loop delay at 400 Hz is >= 5 ms (K20 GM 7.8 dB in the model).

## D-G1.7 Provenance check (S50, 2026-11-17, from owner answer Q4)
Choice: `bench/provenance.py`, used by `run_scenario.py --gate`: refuses on a dirty tracked tree, on a SITL binary whose
generated version header (PX4_GIT_VERSION_STR) is not HEAD, or whose header is newer than the binary; records binary
SHA-256 and SHA-256 of world, model files and params file in run.json (`provenance`, `gate_bearing`). Self-test
`bench/tests/test_provenance.py` break-checked (3 mutations caught). Alternatives: compare only firmware paths between
binary commit and HEAD (fewer rebuilds, but weaker than the owner's wording); hash-only (no refusal). Known limit:
the header holds the commit hash without a dirty flag, so a binary built from a dirty tree at HEAD passes; the binary
hash in run.json lets a reader detect it afterwards. Overturn if: a gate run is found with a binary hash that differs
from the one rebuilt from its commit. Gate analysis scripts must ignore runs with `gate_bearing` false.

### D-RATE-LEAD addendum (S51, review r1 NOT BLOCKING)
Opus review `design/rate_lead_review_r1.md`: law verified against code for roll/pitch. Overturn evidence added: GM < 6 dB
at K_R 20 with ACT_TC overestimated by 40 % (model predicts ~5 dB at K40) -> default MC_INDI_LEAD < 1 or a lower bound
on identified tau_c. Lead is feedback-only (setpoint path keeps the actuator lag); feedforward is a separate later option.

### D-RATE-LEAD addendum 2 (S53): defaults MC_INDI_LEAD 1, MC_INDI_ACT_TC 0.05; identification errs high
Evidence: `results/stage3_s53/act_tc_sweep/README.md` (roll M3a, 800 Hz, plant tau 0.033): ACT_TC x0.5 PM 36/GM 5.1,
x0.6 PM 42/GM 7.9 (fail G2); x1 PM 59/GM 14; x1.5 PM 86/GM 11; x2 PM 75/GM 10 (2 seeds). Tolerance is one-sided.
Choice: (a) MC_INDI_LEAD default 1 (lead 0 gives PM 26 at the stock MC_ROLL_P 8). (b) MC_INDI_ACT_TC default 0.05:
covers any plant tau in [0.025, 0.05] within the measured safe band [x1, x2]; on the reference airframe it is x1.5.
(c) Stage-4 identification reports an upper bound of tau_c (estimate + its uncertainty, never the point estimate
alone), and the user procedure says: if unsure, round ACT_TC up. Applied to firmware with the stage-3 defaults item
(`design/stage3_items_note.md` item 6), not before.
Alternatives: keep 0.02 (fails G2 on the reference airframe); default = plant 0.033 (no margin for an under-estimate,
and plants slower than the reference fail); lead < 1 (lowers PM at matched tau, does not fix the under-estimate side).
Overturn if: pitch/yaw or 400 Hz margins at ACT_TC x1.5 fall below G2; a plant with tau < 0.025 s (default > x2)
shows GM < 6 dB; G6 outlook airframes with slow motors (tau > 0.05) are flown before identification (then the
pre-identification behaviour of decision 3 must cover it).

## D-YAW-INV (S54, IMPLEMENTED S56): yaw inversion consistent with the actuator lag
- Finding (A-27, `results/stage3_s54/yaw_m3a_lf/README.md`): step 8 divides the yaw increment by the static G1 + G2/dt
  (21600 + 205 at 800 Hz) and adds (G2/dt)(t_f - t_f,prev). This is dead-beat spin-up: it assumes the rotor reaches
  the command within one sample. With tau 33 ms the nu and a_f terms are ~1/105 of the G1 law, t_cmd ~ a one-step
  extrapolation of t_f, and M3a reads L ~ -H A_m (-1 at DC). Flight and model agree within ~3 dB / 20 deg to 20 Hz.
  The G2_Y value (D-G2Y-DERIVE) is not in question, the form of the inversion is; the gain depends on dt.
- Option (c), proposed: increment = (nu - (1+c) a_f) / (G1 + G2 (1 - z^-1)/dt), i.e. a first-order low pass with
  time constant G2/G1 on (nu - a_f)/G1 (backward Euler: Delta_k = (nu - (1+c) a_f + (G2/dt) Delta_k-1)/(G1 + G2/dt)),
  no t_f difference term. The plant spin-up (G1 + G2 s) is inverted dynamically, not at the sample rate. Model
  (`bench/yaw_break_model_s54.py`, UNKEYED): with matched G2 the yaw M3a loop becomes K A/s, crossover 1.4 Hz, Ms 1.3 dB,
  as for roll; independent of dt.
- Alternatives: (a) keep the coded law and measure yaw at a plant-only break (does not fix the dt-dependent yaw gain);
  (b) subtract G2 dt_f/dt from a_f and invert on G1 only (closed loop alpha/nu = (1 + tau2 s) A: high-frequency gain
  x34 at 41 Hz, the A-25 limit cycle); (d) G2 0 (A-25).
- Model mismatch (plant G2 x0.5/x2, plant tau x1/x2, `results/stage3_s54/yaw_model/model_out.txt`): option (c) Ms
  1.6-8.1 dB at M3a, worst G2 x0.5 with tau x2; coded law Ms 22-28 dB at M3a. The script's PM read-out is crude
  (phase wrapping, gives negative PM for the coded law that flies): compare Ms only until keyed.
- Keyed S54 (T111, `results/stage3_s54/yaw_model/second_key.md`): AGREE within 0.1 dB after a key-2 denominator fix.
- S55 ACT_TC mismatch and 250/400/800 Hz (`results/stage3_s55/yaw_model/README.md`, UNKEYED extension): option (c)
  dt-independent; inside tau_m >= plant tau and plant G2 x0.5..2, M3a Ms <= 5.9 dB, GM >= 8.2 dB. Outside (tau_m
  under plant and law G2 above plant) down to GM 0.6 dB: stage 4 reports an upper bound of tau_c and a lower bound of G2.
- S55 opus review r1 (`design/yaw_inv_review_r1.md`): NOT BLOCKING; code per its majors (applied-increment state, zero when
  landed/reset, G2_Y text).
- Open before code: (review done), then unit test with the parametrised plant and yaw M3a 2 seeds.
- S56 IMPLEMENTED: 23e9d30cc0 (law, state = applied increment, 0 landed/reset, G2_Y text, 4 tests) + 296766019a (state
  gated by landed on the first landed cycle, haiku second key T114 finding, test break-checked). Yaw M3a 2 seeds
  (`results/stage3_s56/yaw_m3a/README.md`): f_c 1.24 Hz, PM 88, DM 197 ms, Ms 1.6 dB (model 1.4 Hz / 1.3 dB);
  5-40 Hz re-fly GM 18.4 dB at 22 Hz (`results/stage3_s57_pre/yaw_m3a_hf/README.md`).
  Overturn: a yaw M3a with Ms > 6 dB inside the stage-4 tau/G2 bounds, or a yaw limit cycle with G2_Y > 0.
- Overturn if: the model with G2 x0.5..x2 shows a limit cycle or GM < 6 dB, or the flight disagrees with the model by
  more than the G2 tolerance.

## D-G2-DEFER (S57): rate-loop margin table stops at anchors until the stage-6 freeze
- Decision: the stage-3 G2 rate-loop evidence is roll M3a at 800/400/267 Hz (model-only path), yaw 800 Hz, and one
  measured-rotor anchor (roll 800 Hz). Remaining rows (pitch, measured path at 400/267 Hz, linear-model cross-check of the
  measured path) are flown in stage 6 on the frozen pair, where G2 is passed.
- Alternatives: finish the full table now (re-bought at each law change: four law revisions S44-S56 voided earlier rows);
  no anchor at all (risk: a law change breaking margins unseen).
- Reason: route check 57 (`design/route_check_57.md`); every gate is validated on the frozen pair.
- Overturn if: a later inner-loop change moves an anchor by more than 10 deg PM or 3 dB GM, or any anchor drops below
  G2 thresholds -> re-measure the full table before continuing.

## D-G2-OUTER-DEFER (S58): outer-loop break measurements wait for stage-5 code
- Decision: `design/g2_outer_breaks_note.md` stays UNKEYED as a plan; its second key, the A-26 model script and any
  attitude/velocity/position M3b flight are done against the stage-5 outer loop, not the archived `indi_accel_control`.
  Stage-3 safety items (route check 57 rec 2) and the stage-5 hover slice (rec 3) go first.
- Alternatives: key and model now (6-9 sessions on a loop that stage 5 replaces; the M3b injection point
  indi_accel_control.cpp:273 moves with it); drop the note (loses the PID reference-break plan).
- Reason: route check 57 b/c (gate evidence bought before the law is frozen is re-bought); outer breaks depend on the
  stage-5 loop structure (S41 lesson: model contains every loop the break closes around).
- Open point for the key: the reference breaks L = T/(1-T) are ill-conditioned where |T| ~ 1 (below the crossover);
  prefer an additive-input break (velocity/acceleration feed-forward) wherever one exists.
- Overturn if: stage 5 keeps `indi_accel_control` unchanged at the injection point (then key the note at once).

## D-S3-LANDED (S58): landed vs maybe_landed in the INDI rate law (stage-3 item 1)
- Decision: split the flag. `maybe_landed` alone = like the stock PID freezing its integrator: the law runs in full
  (t_fb, lead, yaw state kept), only slow adaptive states (blend integrator) freeze; NO output slew limit in flight.
  `landed` = hard: today's zeroing of t_fb, lead and yaw state; on both edges of `landed` the feedback torque t_fb is
  ramped (not stepped) with slew MC_INDI_LND_SLEW (normalised torque/s, default 5.0, i.e. full scale in 0.2 s).
- Alternatives: note option (slew-limit the published torque while maybe_landed): removes authority during a hard
  descent when the flag toggles falsely in flight; zero everything on either flag (today): trim-sized kick per edge;
  ignore landed: increment winds up against ground contact.
- Overturn if: a G5 false-maybe_landed or touchdown test shows a rate transient beyond its limit, or a ground wind-up.

## D-S3-FROZEN (S58): frozen rotor-speed detection (stage-3 item 4)
- Decision: per motor, frozen iff the reported rpm is bit-identical for MC_INDI_ERPM_FRZ (default 0.5 s) while armed
  AND the motor's commanded u varied by more than 0.02 (max-min over the same window). Frozen motor = offline for the
  measured path (existing invalid -> modelled fallback with hysteresis); mask logged.
- Alternatives: rpm must change every sample (false trips under eRPM quantisation); all four identical (misses one
  frozen motor); DShot error counter (does not see frozen values); note's thrust-setpoint-std condition (indirect).
- Reason: a spinning rotor whose command moves 2 % of range changes speed by far more than one eRPM step; disarmed or
  constant command can never trip.
- Overturn if: a false trip in any G3/G4 run (vibration x1..5, harsh noise) or a frozen-value injection not caught.

## D-S3-SPTO (S58): rate-setpoint timeout (stage-3 item 3, coded later)
- Decision: on vehicle_rates_setpoint older than MC_INDI_SP_TO (default 0.5 s, PX4 offboard minimum 2 Hz), use zero
  rate setpoint, HOLD thrust, flag + rate-limited warning; no thrust decay (descent policy belongs to commander/outer loop).
- Alternatives: note's 0.2 s + thrust decay at 0.5/s (trips a legal 3 Hz offboard rate stream; a controller-level
  descent policy at unknown attitude); hold everything (stock behaviour).
- Overturn if: G5 shows a stale-setpoint case where held thrust causes loss of control before a commander failsafe.
- S59 note: an offboard body-rate stream at exactly 2 Hz sits at the 0.5 s limit and can trip for 1-2 cycles (rates
  zeroed briefly, recovers on the next message); G5 offboard test flies >= 10 Hz. Coded S59 (T119), see `design/t119_s3_items_s59.md`.

## D-S5-SLICE (S60): stage-5 hover slice scope, parameter name, archive pointer
- Decision: first stage-5 code is a hover slice of architecture A: A1 (in-place rewrite, start by parameter), A2, A3
  (tracking/bypass outside FLIGHT, RAMPUP under bypass = A8), A5, A6, A7, A9 (shell copy of MulticopterPositionControl,
  stock PositionControl/Takeoff libraries), A13/A14 (LIB entry at a_ref). Deferred to the next slices: A4 XY-margin
  port (slice uses tilt limit + collective clamp), A10/A15 acceleration-only groups, decision-2 remedy (A11: chosen
  after the thrust-gap flight on this slice).
- Last commit of the archived external-mode module before the rewrite: 41326ec474 (A1 record).
- Parameter: `MC_INDIP_EN` renamed `MC_INDI_POS_EN` (A12 N6, archive meaning differs).
- Alternatives: full A in one step (too large for a $3 session, lesson 21); keep the archived module and test the
  thrust gap on it first (buys evidence on a loop that A replaces, route check 59).
- Overturn: slice hover fails the pre-test gate for a structural reason (not a parameter), or take-off shows the A8
  overturn signs (A12 N5) -> design A8' before continuing.

## D-S3-ATT-STEP (S61): attitude step overshoot under INDI -> rate-setpoint lead (owner note N1 B)
- Finding (`results/stage3_s61/README.md`, 3 seeds): INDI roll/pitch overshoot 12.6-14.2 %, settle 655-870 ms (PID 0 %,
  380-412 ms). Cause: D-RATE-LEAD is feedback-only (addendum S51 said so); closed rate loop tau s^2 + (1 + K tau_c) s + K,
  dominant pole 12.6 rad/s = 79 ms (flight fit 80 ms, a_f = 0.48 nu); MC_ROLL_P 8 on it -> zeta ~0.6 + delay.
- Choice: put the same prediction on the setpoint path: nu = K (r - w) + c r_dot_f, numerator nu - (1 + c) a_f as
  coded, i.e. nu_eff = K (1 + tau_c s)(r - w) with c = lead_scale K tau_c as coded (same bound kMaxLeadGain), r_dot_f = derivative of the rate setpoint through a first-order
  filter (tau ~ 10 ms) and a magnitude clamp, off when landed or when the setpoint path is reset (mode switch, timeout,
  first cycle) to avoid an impulse. Closed rate loop -> K/(s + K) with tau_c = plant tau. Feedback loop unchanged, so the
  G2 rate-break margins (M3a) are unchanged; only the setpoint path and the attitude loop change.
  Model prediction (attitude step, P 8): overshoot 0.6 %, settle 388 ms; full r_dot feedforward (gain 1 + K tau_c) 0 %,
  705 ms (slower, rejected). No new parameter: gain follows MC_INDI_LEAD, K, ACT_TC (generic, F-3).
- Alternatives: (a) lower MC_ROLL_P under INDI: settle ~600 ms, fails G2-STEP, rejected; (b) raise K_R: rate margins fall
  (S49 sweep, K40 fails); (c) reference model / prefilter on the attitude setpoint: removes setpoint overshoot only, the
  disturbance response stays underdamped; (d) full r_dot feedforward: slower (model 705 ms) and more setpoint-noise gain.
- Open before freeze: second key of the model and of the code; noise of r_dot_f in acro (stick) and in attitude modes
  (G4); attitude-break margin (G2) with the new setpoint path; yaw (G2_Y spin-up term, same form with K_Y).
- S62: coded da64bc26b3 (+ b8866cd4b1). The term sits in the INDI numerator, not in nu: logged nu excludes it, the
  derivative is logged as rate_sp_dot. Flight seeds 1-3: OS 0.2-1.0 %, settle 358-394 ms (model 0.6 % / 388): agrees.
- Overturn if: flight on >= 2 seeds disagrees with the model prediction by > 5 points of overshoot, or r_dot_f raises
  motor-command RMS in hover beyond the G4 limit, or a mode switch shows a setpoint impulse that the reset does not catch.

## D-GAP (S70, PROPOSED; S71 opus r1 BLOCKING `design/dgap_review_r1.md`, amended below; sonnet r2 `design/dgap_review_r2.md` OPEN on wording, fixed S71 -> ACCEPTED for implementation): decision 2 for the outer loop
- Evidence: `results/stage5_s70/README.md` (T156, 1 flight each, seed 1). Position hold, 4 motors x0.85 thrust:
  INDI outer loop standing z error 0.31 m (HTE on) / 0.37 m (HTE frozen); prediction (1-s)g/(Z_P Z_VEL_P_ACC) 0.368;
  stock mc_pos_control 0.01 m (HTE on), 0.06 m (HTE frozen, vel integrator on), 0.37 m (both off). Single motor 0.8:
  INDI 0.19 m. A11 mechanism confirmed: measured collective (mean_u from eRPM) cancels the implicit integral.
- Choice: (d) the rate loop's complementary blend applied to the measured collective: coll_f = coll_meas +
  LP_tb(coll_model - coll_meas), so measured at high frequency, modelled at DC (integral action restored; sag and
  weak motors appear as omega drop and are absorbed). One mechanism in both loops (rate: `setActuatorBlendTimeConstant`).
  tb set from the measured outer-loop margin (G2), not tuned for the gap metric.
- Alternatives: (a) slow per-motor command-to-omega^2 correction applied to the measured state of both loops (more
  machinery, motor-health side benefit; fallback if (d) costs margin); (b) integrator on the acceleration error in the
  module (new state, outer only); (c) stock MPC_*_VEL_I_ACC integrators (stock-tuned, absent in acceleration-only
  setpoint groups A10/A15, leaves a standing acceleration error).
- Overturn: (d) gives < 45 deg phase margin on the INDI acceleration/velocity break at a tb that removes the gap within
  10 s, or the blend reproduces the stage-1 0.1 s blend failure in the collective channel.
  S71 r1 replaced this criterion (item 3 below): the phase cost at crossover is bounded by asin((1-k)/(1+k)) (k = thrust
  scale, ~4.7 deg at 0.85) whatever tb is, so the 45-deg test could not fire. Real risk: a lightly damped HF mode,
  because the model path has no motor lag.
- S71 amendment (answers r1 items 1-5; the r1 BLOCKING finding was that the rate-loop blend, `indi_rate_control.cpp`
  :336-345, SNAPS its state to the instantaneous gap when landed / blend off / telemetry invalid, against A16):
  1. Blend state b = LP_tb(coll_model - coll_meas), kept in u units, bounded (|b| <= 0.3), logged in indi_pos_status.
     Edges: b is FROZEN (held, not reset) on ground (landed / maybe_landed), at A3/A8 bypass and e7 edges (A16);
     the module's reset() does not touch b; while mean_u is invalid (telemetry loss or frozen) b is frozen and
     coll_f = coll_model; while the collective is clamped (module limit or allocator collective-saturation flag) b
     is frozen (anti-windup; if the allocator exposes no collective-saturation flag, the module's own clamp and
     the measured mean_u at its limit are used). b starts at 0 at boot only (S153: at every arm, D-PREFREEZE-R1 F2). Recovery: when the freezing condition
     clears, b resumes integrating from its held value (no snap, no reset), and coll_f switches back to
     coll_meas + b on the first valid mean_u sample. The rate-loop snap is NOT copied; whether the rate loop
     itself should freeze is filed for the stage-3 safety review (ANOMALIES/STATE).
  2. coll_model = previous clamped collective command (no actuator model), passed through a second delay/LPF path
     parallel to the measured one in `indi_accel_control` so both sides are time-aligned.
  3. Overturn: (d) is reverted to (a) if the measured acceleration-loop response at tb and at tb/3 shows a lightly
     damped HF mode (resonance peak > 3 dB or step overshoot > 25 %), or the G2 velocity-break PM is < 45 deg, i.e.
     if NO tb in the window passes both tests. Window: ~0.3 s (HF mode) to ~2.5 s (gap removed within 10 s). tb is the default 1.0 s unless
     the margin measurement moves it.
  4. MPC_XY/Z_VEL_I_ACC stay 0 under INDI (no double integrator); (d) runs in acceleration-only setpoint groups
     (A10/A15) too, since it acts on the collective, not on the velocity error.
  5. Lesson-20 tests: unit test on a plant with thrust scale 0.85: steady collective error after 10 tb is
     < 0.01 (u units) with tb = 1 s, and >= 0.9 (1-k) with tb = 0 / blend disabled (negative control). Freeze
     tests, each asserting b unchanged (|db| < 1e-6) across the edge and resuming without a step afterwards: landed
     edge, telemetry-loss edge and its recovery, module reset() call, collective clamp, A3/A8 bypass, e7. Each test
     is checked by breaking the rule once (snap or reset b) and seeing it fail. Flight check: gap085_indi_htoff and
     loss08_indi standing |dz| < 0.06 m (the stock result with its integrator); land/re-take-off with the gap
     present: |b| after re-take-off within 10 % of its pre-landing value and max |dz| in the first 5 s after
     take-off < 0.15 m.

## D-RATE-BLD (S73, ACCEPTED S79; precondition 2 settled S75 by D-RATE-BLD-EDGE): decision 2 for the rate loop = the existing complementary blend, ON by default
- Evidence: A-33 (`results/stage5_s73/README.md`). With MC_INDI_ACT_BLD = 0 (firmware default) one motor at 0.8
  holds a 10.4 deg standing attitude error (rate error ~1 rad/s) because measured actuator state removes the
  integral action (lesson 9). Blend 0.3 s and 1.0 s both remove it (sp-vs-actual 0.05 / 0.06 deg).
- Alternatives: (i) blend ON (one mechanism with D-GAP, `setActuatorBlendTimeConstant`); (ii) slow per-motor
  correction of the command-to-omega^2 map (learns the weak motor directly, also absorbs sag, but a new estimator
  with its own margins and landed/telemetry-loss edges); (iii) an explicit rate integrator on nu (duplicates the
  attitude-loop job, windup under saturation). Choice (i): already coded, tested, and shared with D-GAP.
- Value: proposed default 1.0 s (same tb as D-GAP; smaller post-event transient than 0.3 s, 0.046 vs 0.107 m, one
  seed). Before the firmware default changes: (1) rate-loop M3a margins at tb 1.0 and 0.3 (lesson 10: stage-1 0.1 s
  crash unexplained; margins must show why 0.1 fails or that it does not); (2) the snap-vs-freeze edge of the rate
  blend (D-GAP r1: `indi_rate_control.cpp` snaps its state to the instantaneous gap when landed / off / telemetry
  invalid) settled and break-tested; (3) a unit test with a weak-motor closed-loop plant that fails with tb = 0.
- Overturn: margins at tb 1.0 below the G2 thresholds, or a G3 pre-test where the blend's DC model path diverges
  (G1 error x2, telemetry loss) -> option (ii).
- S76: precondition 1 met at 800 Hz roll (`results/stage3_s76_bld/README.md`): PM 68 deg, GM 16 dB, DM 43-46 ms at
  tb 1.0/0.3/0.1, no tb effect (blend corner below the 4 Hz crossover); the stage-1 0.1 s crash is not a rate-loop
  margin at hover on this airframe. Open: 400 Hz, D-GAP velocity-break items, A-34 (PM shift vs S57).
- S77: preconditions 2 and 3 met: edge break tests and a weak-motor closed-loop test (tb 0: 0.25 rad/s standing
  error, tb 1: 1.6e-5) committed 499e1df991, each break-checked (`results/stage3_s77_tests/README.md`). A-34 traced
  to the setpoint lead da64bc26b3, not the blend (`results/stage3_s77_a34/README.md`). Left before the default
  changes: the D-GAP velocity-break items. 400 Hz flown S77 (`results/stage3_s77_400/README.md`): PM 70 deg,
  GM 13.3 dB, DM 51 ms at tb 0 and 1.0: precondition 1 met at 400 and 800 Hz (roll).
- S79: ACCEPTED, firmware default MC_INDI_ACT_BLD 1.0 s (a94d5c181a). The D-GAP velocity-break items concern the
  outer loop's own blend, not this rate-loop default (route check 79); they stay a D-GAP precondition.

## D-RATE-BLD-EDGE (S75, DECIDED): rate blend restarts at the instantaneous gap; D-GAP keeps its freeze
- Question (D-RATE-BLD precondition 2): the rate blend (`indi_rate_control.cpp` 5d) sets `_blend = t_gap` whenever
  it is not active (measurement not in use, tb = 0, landed) and `reset()` zeroes it; D-GAP freezes its bias `b` on
  every edge. Should the rate blend freeze too?
- Analysis (code read S75, survey `design/rate_blend_survey_s74.md`): the two states are different objects. The
  rate `_blend` is the low-pass part of a complementary filter, output `t_f_meas + LP(t_model - t_meas)`; its correct
  initial value is the current gap, which already contains any steady gap (weak motor, sag), so restarting there is
  bumpless (output = model at the switch) and loses nothing. D-GAP's `b` is a learned bias of the thrust model that
  cannot be re-derived from one sample, so it must be held. While the blend is inactive the output is the model path
  (or pure model when landed: `t_f_meas + t_gap`), which keeps the integral action of model-feedback INDI.
  `reset()` zeroing `_blend` is harmless: `resetStates()` also zeroes `_meas_valid_cycles`, so the next 20 cycles
  track the gap before the measurement is used. Frozen-but-valid telemetry is a separate item (stage-3 frozen
  detection), not a blend edge.
- Choice: keep the current semantics (track/snap when inactive, freeze the integrator on maybe_landed, hold on the
  fault path). No firmware change. Alternatives: freeze on loss/landed (D-GAP style: a bump of the high-frequency
  gap at recovery, no benefit since the steady gap is re-captured at once); one shared helper with D-GAP (would force
  one semantics on two different states).
- Remaining for D-RATE-BLD: break tests of these edges in the unit tests (recovery after loss with a steady gap:
  no step in t_f; landed->airborne: no step) and the weak-motor closed-loop test that fails with tb = 0.
- Overturn: a flight or unit test showing a torque step at telemetry recovery or take-off larger than the
  high-frequency gap, or a G3 telemetry-loss run whose post-recovery transient exceeds the G3 limits.

## D-G2-PINJ (S82): outer-loop break injected at the INDI stage input, bench parameters MC_INDI_PINJ_*, off by default
- Choice: d (Schroeder multisine, generator copied from the rate module's module-local IndiInjection) is added to
  the stock position-loop acceleration output c; u = c + d is the INDI stage's a_ref, so the thrust vector, previous
  thrust command, D-GAP blend model path and jerk difference all use u. L = -G_cd/G_ud is the velocity/position loop
  with the INDI acceleration loop closed (serves the D-GAP velocity-break overturn test). With AX = 0, u == c.
- Alternatives: d at the stage output (thrust/collective): that is the INDI acceleration-loop break, still needed
  for G2 as a second injection point; injection in mc_pos_control (O-11 zero diff, excluded).
- Overturn if: the AX = 0 flight is not bit-identical to the build without injector, or the measured L disagrees
  with the linear model beyond the G2 tolerance without an explained cause.
- S84 addendum (D-G2-PINJ-OUT): MC_INDI_PINJ_PT 1 moves d to the stage output (u_o = t_c + d to the attitude
  setpoint; library previous command set from the applied collective, setAppliedThrust). This break closes every
  path through the plant input, so with a matched actuator model the INDI incremental terms cancel and L is
  dominated by the outer loops; the INDI-specific part (mismatch, D-GAP blend) is read above ~3 Hz. Alternatives:
  break inside the library between t_f and t_c (isolates INDI's mismatch loop but is not a physical loop-break
  point), or none (G2 would lack the plant-input cell). Overturn if: the output-break L at crossover differs from
  the input-break L by more than the G2 tolerance without an explained cause, or the second key finds the applied
  command and the library state inconsistent.

## D-HOLE-EXCESS (S88): log-hole limit per topic, as excess over the nominal period (tool-spec fix, G1/G2 evidence)
Max hole per topic from RAW timestamp gaps, before duplicate cancelling (T184 escape: a k=2 gap next to a duplicate
left the list). A gap is a hole when gap - median(raw dt) > 10 ms; count checks unchanged. Reason: a flat 10 ms
failed an 89 Hz topic (period 11.2 ms) on one 18.75 ms gap with nothing lost. Alternatives: flat limit (rejected,
rate-dependent), limit in periods (rejected: at 400 Hz one period is 2.5 ms, too strict for the analysis).
Effect: s86 pt0_ax3_r800_s2 FAIL->PASS; 27 other cells unchanged (results/stage5_s85_holes/fixes_s88.md).
Overturn if: a cell passing under this rule shows a coherence or margin defect traceable to a logging gap.

## D-HOLE-FREEZE (S89)
hole_report.py frozen at 688f198ab2 for G2/G3 evidence. All serial G2 outer cells PASS (results/stage5_s85_holes/rerun_s89.md).
Alternatives: keep fixing open T188 minors (max_excess under-reported below 1.5x median: report only; median-0 topic
raises loudly). Reason: route check 89, five sessions of tooling with no gate change. Overturn if a hole_report verdict
is shown wrong on raw timestamps of a gate log, or a loud error blocks a gate cell.

## D-GATES-G3G8 (S94)
G3-G8 test text frozen in GATES.md "G3-G8 FINAL (S94)" with 8 orchestrator decisions: no quota on G3 accuracy items
(every miss in a valid run fails and is explained), owner-floor ranges not narrowed (delay line and GNSS latency hooks
to build), G4 limits fixed from sources before any G4 measurement, G6 full G3 on the worst-converged identified set.
Alternatives: 95 % quota on accuracy items (rejected: weakens "within stated limits"); freeze thresholds after the
pre-test (rejected: fits the test to the result); full G3 per wrong start (10 x 300 runs, cost). Overturn: owner
answer on G6 sample size, or a G3 pre-test spread > 1/3 of a limit (then owner question, no silent change).

## D-ALTCTL-Z (S97): INDI serves climb-rate-only modes (ALTCTL) on the vertical axis only
F-2 requires ALTCTL on the INDI stack; today want_indi needs position or velocity control, so ALTCTL bypasses INDI.
Decision: want_indi also accepts flag_control_climb_rate_enabled; when neither position nor velocity is controlled the
stage runs z-only: the thrust direction is the stock one (stick tilt, unchanged pilot feel), the collective comes from
the INDI vertical increment t_cz = t_fz + (a_cz - a_fz), collective = t_cz / dir_z, limits as usual; omega_ff = 0.
Alternatives: full 3-axis stage with a_ref xy = stick acceleration (rejected: INDI cancels measured drag in xy, so with
centred sticks the vehicle keeps its ground speed indefinitely instead of slowing, a change of ALTCTL semantics);
leave ALTCTL on the stock integrator (rejected: F-2, and lesson 9 gap then handled only by PID I).
Overturn: a G5 ALTCTL flight with a z transient or oscillation at the mode switch, or the owner asking for INDI xy in
ALTCTL.
Scope note (T205): want_indi accepts any climb-rate-only mode, so the DESCEND failsafe (and any other climb-rate-only
nav state) also runs the z-only stage. Intended: F-2 covers failsafes, and DESCEND has the same semantics as ALTCTL
with neutral sticks. G5 flies it.

## D-G7-HARNESS (S98): module-level tests of mc_indi_pos_control via extracted pure helpers, SITL for wiring
- Problem (T205 MAJOR 6): the module's decision logic (want_indi flags, z_only derivation, the T203 pre-update
  integrator gate with its age constant and validity checks) has no test; G7 asks for module-level tests that fail
  when a behaviour is broken.
- Options: (A) uORB functional gtest that instantiates McIndiPosControl (heavy: work queue, parameters, many topics;
  no precedent in the stock MC modules); (B) move the pure conditions into a small header in the module (precedent:
  IndiPosInjection.hpp + IndiPosInjectionTest.cpp, px4_add_unit_gtest) and unit-test them, the module calling them
  unchanged; (C) SITL flights only.
- Decision: B now (one sonnet task after T206), C for the wiring (G5 flights already exercise it). A is not built
  unless a G7 reviewer finds a wiring defect B and C both miss.
- Overturn if: a defect is found in the glue between the helpers and uORB that neither the unit tests nor the G5
  flights caught.
- Amended S98 per route check 98: implementation of B deferred to stage 7 (G7 packaging); until then the module
  logic is covered by G5 SITL flights. No further coverage tasks before the G5 pre-test.

## D-G3-SAMPLER (S108)
Sampler `bench/g3_sample.py` choices (details design/g3_sampler_s108.md): saturation only in corner C3 (10 of 300
runs; GATES text "10 % of runs (inside the corner set)" contradicts C3 = 10 runs; it is a beyond-range widening, class (b),
so 10 runs suffice); wind steady 0-5 m/s drawn in every run as the factor table says, so "calm" limits apply only where
the draw is near 0 (to settle in g3_checks: calm = steady < 1 m/s and no gust); pre-test = 15 grouped extremes + 5 sampled.
Alternatives: 30 saturation runs outside corners; wind in a fraction of runs. Overturn: second key or pre-test shows the
calm/wind split leaves item 3 calm limits untested, or the owner reads the saturation share as 30 runs.

## D-G3-SAMPLER-K108 (S109): resolution of K108 MAJOR findings
- M1 saturation share: kept at 10 runs (C3), per D-G3-SAMPLER. No change.
- M2 gust: whenever wind is drawn, gust amplitude >= 1 m/s above steady and total peak <= 9 m/s (owner cap): draw
  peak U[3, 9], then steady U[0, min(5, peak - 1)]; C4 pins steady 5 and draws peak U[6, 9]. Alternative: gust on top of
  steady (total could reach 10 > owner 9 m/s cap). Overturn: owner reads the 9 m/s as gust amplitude, not total.
- M4 G1 error: the drawn factor e in [0.5, 2] (log) IS the realised controller/plant ratio (spec S64 text). The rate-loop
  plant G1 scales as 1/inertia_scale per axis, so the controller G1 multiplier written to the run is e / I_scale
  (plant G1 = G1_nom / I_s, controller = k G1_nom, ratio k I_s = e). Mass does not enter the rate-loop G1. Dynamic
  thrust loss (sag, weak motor) lowers plant G1 further during the run; it is a separate G3 axis and is recorded, not
  compensated. The run record holds e, I_s, k. Alternative: multiplier on nominal (realised ratio 0.35-2.6, outside
  the owner range). Overturn: an identified G1 on a variant model disagrees with G1_nom / I_s by more than 10 %.
- M3: the self-test gets a guard for every surviving mutation listed in K108 (asym log law, GNSS latency law,
  mismatch sign range, sag/weak law, weak/loss motor index spread, loss/frozen durations, sag ramp).

## D-G3-STICK-FACTORS (S117)
- Rule: in mode stabilized or acro the sampler draws only attitude/rate factors (G1, tau, asymmetry, delay, mass, inertia, telemetry, vibration, GNSS); thrust_sag, saturation, weak_motor and wind are set to nominal "off" with `not_drawn`. Corners C2, C3, C4, C6 (pinned sag, saturation, wind, weak motor) are forced to position (`mode_forced`); pretest extremes x_sag, x_weak, x_saturation, x_wind already fly position. C1, C5 and free draws keep the drawn mode (RNG order unchanged).
- Reason: S116 ladder (results/g3_ladder_s116/README.md): PID and INDI both trip the height watchdog with sag 0.7 / weak 0.8 in stabilized stick (open-loop collective, no altitude hold), so those runs test the scenario, not the controller.
- Alternatives: draw everything in every mode and count watchdog trips as scenario failures; add altitude hold to the stick scenario; give stick runs altctl.
- Consequence: thrust and wind coverage only in position-mode runs (about 70 % of free runs plus the thrust/wind corners). altctl/posctl stick scenarios are not in MODE_MIX and stay out of the first probe batch until metrics.py has a reference/window for them (RC113 stop rule).
- Overturn: a stick scenario with closed-loop altitude (e.g. altctl) enters the batch; thrust factors can then be drawn there.

## D-G3-STICK-PILOT (S117; implemented S118 880a83c63b; pre-test T118 PASSED S119, decided)
Stick scenarios get a simulated pilot in the runner: a slow altitude PI on throttle (about 0.2-0.3 Hz, applied
around the hover throttle) in stabilized and acro, and in acro an attitude-levelling term (rate command = stick -
k x attitude, k about 1-2 /s) so the pilot behaves like a human holding the vehicle. Reason: S117 probe run_000 (acro)
sank 3.5 m with INDI and 2 m with PID in the same window, PID then held 32 deg tilt and climbed to 159 m: the open-loop
stick scenario tests chaos, not the controller (results/g3_probe_s117/README.md). Alternatives: drop acro from G3
(F-2 requires acro, G5 then carries it alone); widen the watchdog (weakens the test); stick input on rate only with an
external altitude hold (no PX4 mode does that). With the pilot loop, thrust factors may be drawn again in stick modes
(overturn condition of D-G3-STICK-FACTORS). Overturn: the pilot loop bandwidth interacts with the controller under
test (pilot loop closed > 1/5 of the attitude bandwidth), or a human-pilot model from the literature disagrees.
S118 addendum: pilot active from the manual-mode switch (neutral rows included), not only in the stick segment (v0
flight tripped in the neutral segment); integral clamp = thr0, total thrust clamped to the stick range (K118
MAJOR-1). RC118 time-box: if acro idx 0 fails for INDI and PID with the pilot, acro is G3-unprobed and G5 carries it;
alternative kept (RC118 sec 3): stabilized/acro as stick-step-and-release recovery scenarios without a pilot.
S119 result (results/g3_pilot_s118/README.md): idx 0 (acro), 21, 49 fly the full window with INDI and PID; segment
altitude means 4.5-6.2 m vs 5 m, acro tilt 0.0-0.1 deg before LAND; stabilized vz follows the demand (corr 0.99,
gain 2.0-2.2, same INDI/PID), so the pilot does not cancel the input (K118 MAJOR-2 closed by measurement).

## D-IDENT (S119 proposed, S120 DECIDED: owner Q6 answer B): identification concept (decision 3) and default set (decision 4)
- Choice proposed: `design/ident_concept.md`. One closed-loop-aware estimator family (IV regression on measured
  rotor speed, injected multisine as instrument, intercept, saturation excluded) for G1/G2_Y, actuator fit for
  ACT_TC/W_MAX/thrust curve, correlation lag for ERPM_DLY; MC_INDI_DELAY computed from filters. Before identification
  INDI flies a conservative ident configuration (gains halved), full gains gated by an ident-status parameter.
  Defaults: bandwidth gains transfer; physical parameters have conservative ident defaults only.
- Alternatives: A ident under PID; C offline-only ident, refuse to arm; D online adaptive (see note sec 3).
- Overturn: note sec 5 (M1 vs derived > 15 % unexplained; ident gains not holding 6 dB/45 deg at G1 x0.5; no
  convergence to 10 % from x2/x0.5 starts).
- S120 owner (Q6 = B): INDI flies its own manoeuvre in the ident configuration. Acceptance conditions, each a
  test before the procedure counts: (i) start independence, SITL ident from G1 x0.5/x1/x2 gives the same estimate
  (spread <= 10 %) and each within 10 % of true quad5in (estimate following its start = B fails); (ii) multisine band
  chosen against the halved-gain bandwidth, per-axis instrument strength (first-stage F) and CI reported, weak
  instrument = failed ident; (iii) regressor and regressand through the same filter and delay, deliberate-mismatch
  self-test must fail; (iv) four independent excitation directions, regression conditioning reported; (v) once in
  SITL, same estimator on a PID-flown manoeuvre agrees within tolerance. SITL validates the estimator only.

## D-IDENT-J (S125): Hansen J is a reported diagnostic, not an acceptance gate of the ident fit
- Fact (K125, design/key_k125_fix_k124.md): the J/df <= 20 gate passes every real log (J/df 14.8-15) and cannot
  reject; J/df ~15 means the static model alpha = G1 u + c is rejected across instrument lags on every SITL log,
  while G1 lands within 0.6 % of the derived value from x0.5/x1/x2 starts and at halved gains (fit_s124.md).
- Choice: keep J and the min-J latency shift in the output and the evidence tables, drop "J/df <= 20" from the
  pass list wording (it stays as a printed flag). Acceptance rests on robust F, CI, interior latency shift, filter
  chain match, excluded fraction, and D-IDENT (i) start independence against truth.
- Alternatives: tighten J to a chi2 critical value (fails every correct real log: not a usable gate); keep the 20
  threshold (a gate that cannot fail, K125 says so).
- Likely cause of the misfit (open, K124 MAJOR 7): regressor is a zero-order hold of actuator_torque_measured
  (new value every ~2.4 samples), plus unmodelled actuator lag in u_meas. Overturn if: a held-regressor-free fit
  (interpolated or rpm-rate regressor) drops J/df below ~3 and moves G1 by more than its CI, or a G1 x0.5/x2 plant
  variant (true G1 changed, not the start) is identified outside 10 %.

## D-IDENT-STOP (S126, from RC126): identification frozen until stage 5 has multi-mode code
Decision: no further estimator work before the stage-5 build. Roll/pitch ident stands (within 0.8 % of derived).
Yaw: firmware keeps the derived G1_Y 205.3 (source chain design/a43_closing_s126.md); the production yaw fit is
known biased -20 % by the omitted damping term (A-43 closed) and is fixed before G6 (probe V3: rate regressor +
matched grid, K126 MAJORs; A-44 tracks the +3/+7 % residual). Stopping rule for that fix: G1_Y within 5 % of the
source value on two logs, then stop. Note: probe V3 met D-IDENT-J's overturn trigger on yaw (J/df 2.6, G1 moved
beyond CI): J did detect a model error; re-decide J's role in the same pre-G6 fix.
Alternatives: fix the yaw fit now (1 session, delays stage 5 again); drop yaw identification and derive it (breaks
D-IDENT (i) for yaw). Overturn if: G5/G3 probes show the yaw loop sensitive to a 20 % G1_Y error, or the owner asks
for complete identification before stage 5.

## D-DEFAULTS-FW (S128): firmware defaults and ident-status gate (implements D-IDENT "full gains gated by an ident-status parameter")
- Choice: new int param MC_INDI_ID_OK (default 0). 0 = not identified: the module scales the rate bandwidth gains
  MC_INDI_K_R/K_P/K_Y by 0.5 (pure lib function, unit-tested); 1 = identified, gains as set. Firmware G1_R/P/Y/G2_Y
  defaults move to the quad5in derived values (1757/1640/205/27, defaults_s127.md): a G1 above the true value lowers
  the effective loop gain (gain x G1_true/G1_set), so the reference values are the conservative side for every
  larger airframe, while the old 320/210/30 would multiply the loop gain 5-8x on quad5in. W_MAX stays 0 in firmware
  (pure airframe quantity, 0 = modelled path) and is set to 2700 in the quad5in airframe file. ACT_TC stays 0.05
  until the 1-flight pretest of 0.033 (K127 MAJ2). Bench runs that intend full gains set MC_INDI_ID_OK 1.
- Alternatives: (a) keep generic low G1 defaults (rejected: aggressive side); (b) refuse to arm until ID_OK=1
  (rejected by D-IDENT B: INDI must fly its own ident); (c) scale gains inside the lib config struct by a
  user-visible multiplier param (rejected: one more tunable, not a status).
- Overturn: G2 cells at ID_OK 0 below 6 dB/45 deg on quad5in at G1 x0.5 start; or G6 outlook airframe whose true G1
  exceeds 1757 (then defaults are no longer the conservative side for it).
- S128 amendment (pretest results/act_tc_s128): ACT_TC 0.033 and 0.05 both fly hover and step_roll on quad5in at
  ID_OK 1 (hover indistinguishable; step motor-command activity 20-25 % lower at 0.033; one seed). quad5in params
  file takes 0.033 (model tau, ref_airframe_model.md). Firmware default stays 0.05: an assumed actuator faster than
  the plant is the aggressive side (lesson 8, H5), so the slower value is kept for unidentified, larger airframes.

## D-STAGE-STALE (S130, F-1, closes the in-flight bypass of g5_build_list.md section 0)
SUPERSEDED in part S134 by F-7 / D-F7-GROUND: the `want_indi` false stock path for landed/ramp is removed; (a) and (b)
stand.
- Context: in flight with the stage requested (`want_indi`), stale attitude/acceleration, non-finite a_ref, rate
  < 5 Hz or `IndiAccelControl::update` false made IPC publish the stock attitude setpoint and re-engage the stock
  velocity integrator (IPC:287-295, 851): a PID fallback, against F-1. The start-up `|| mc_pos_control start` is
  removed (D-start-fallback, S12, had decided it but rc.mc_apps still carried it).
- Decision: once `want_indi` is true the stock thrust is never published and the stock integral stays reset.
  (a) Acceleration stale or non-finite: the stage runs on the MODELLED specific force f_b = (0, 0, -G c_prev) with
  mean_u invalid and the blend held. With measured = modelled the increment reduces to the model inversion
  t_c = a_ref - g of the same a_ref (the O-5 modelled-fallback rule applied to the acceleration channel).
  (b) Attitude stale/invalid, a_ref non-finite, rate < 5 Hz or update false: hold the last INDI attitude setpoint
  and thrust (zero-order hold); the attitude controller is equally blind in these cases.
  Each degraded cycle is flagged in `indi_pos_status`; a degraded state lasting > 0.5 s is reported (instrument).
  `want_indi` false (disarmed, landed/ground contact, takeoff state < flight, manual modes) keeps the stock path:
  ground handling and the takeoff ramp, where the measured acceleration contains the ground reaction and INDI cannot
  act. T3/T4 measure the edges.
- Alternatives: hold-last for every case (rejected: open loop in thrust during a long accel outage, the P/D loop
  could not act); refuse to fly / force failsafe (rejected as sole remedy: the estimator failsafe already handles the
  loss of attitude; the stage must still output something until it acts); keep the stock bypass (rejected, F-1).
- Overturn: a G3/G5 run where (a) diverges while the stock mapping would not, or the owner classing the takeoff
  ramp as a PID fallback. UNVERIFIED: arming is not refused when the INDI module fails to start (commander zero diff).

## D-HANDOVER (S132, closes the cause of A-45): bumpless transfer of a_ref at bypass -> INDI
- Cause (design/a45_cause_s131.md, S132 section): on the first stage cycle `want_indi` zeroes the stock velocity
  integrator, which during the takeoff ramp held +2.67 m/s^2 (z, down). a_ref steps -0.61 -> -3.28 m/s^2 and INDI
  delivers it: 2.67/g x hover 0.137 = 0.037 predicted vs 0.035 measured. The 180 ms without `indi_pos_status` is the
  logger subscribing late (first publication), not a bypass.
- Decision: on the first stage cycle after bypass, add o = a_bypass_last - a_ref to a_ref and decay it as
  exp(-t/tau), tau = 0.5 s (2/MPC_Z_VEL_P_ACC at the default 4; slower than the vertical velocity loop so the
  0.1 s handover step is < 10 % hover). All three axes. Not an integrator (fixed decay, no error input): F-1/D-GAP
  unchanged. Pure class `HandoverBlend.hpp`, unit tested.
- Alternatives: keep the stock integrator and let it unwind (rejected: D-STAGE-STALE A2, two gap removers); slew-limit
  the collective (rejected: acts on the output, hides any later real step, axis-blind); start INDI already in rampup
  (rejected: ground reaction in the measured acceleration).
- Overturn: G5 take-off/mode-switch transient still > limit, or a G3 run where the decaying offset delays recovery.
SUPERSEDED S134 by F-7 / D-F7-GROUND (overturn condition met: owner classes the ramp stock path as a fallback). With
no stock integrator there is no bypass -> INDI edge; HandoverBlend is removed once nothing uses it.

## D-F7-GROUND (S134, F-7): INDI law from arming; ground and ramp handled by the modelled specific force
- Decision: the stage runs whenever armed in a position-controlled mode. While on ground (takeoff state < rampup, or
  flight with `ground_contact`/`maybe_landed`) and during rampup, the stage uses the MODELLED specific force
  (existing D-STAGE-STALE (a) path: f_b = (0,0,-G c_prev), gap remover frozen, mean_u invalid). a_ref comes from the
  same stock setpoint chain: on ground the stock +100 m/s^2 down setpoint gives minimum thrust; in rampup the stock
  vz ramp from -g/MPC_Z_VEL_P_ACC gives a collective rising from 0 by model inversion. From flight without ground
  contact: measured f_b, gap remover runs. Stock velocity integrator reset from arming; stock thrust never published.
  Removed: HandoverBlend, bypass hover-thrust sync, the `want_indi` false stock branch.
- Edge step predicted = thrust-model error at the edge (measured - modelled specific force), a few % of hover with the
  identified model (S128 defaults).
- Alternatives: keep a decaying offset at the edge (only if the measured edge step exceeds the limit); blend f_b
  modelled -> measured over tau (same, second step); estimate the ground reaction (rejected: complex, F-9).
- Overturn: G5.4 edge step > 10 % hover or dip > 0.3 m on any seed; landed/ramp windup seen in a log.

## D-KY (S137, decision 4, fixes the G5.1 acro yaw failure): default MC_INDI_K_Y 10 -> 20 rad/s
- Cause (log, results/g5_g51_s136 + g5_g51_ky20_s137 README): yaw t90 0.23 s = first-order lag 1/K_Y at K_Y 10;
  no motor saturation (0.08-0.19), YAW_CUT 0. First-order arithmetic over the G5.1 windows: 15.5 deg/s predicted,
  15.0-16.0 measured. K_Y 10 was inherited from the archive defaults, never justified; roll/pitch use 20.
- Decision: K_Y 20 (same bandwidth as roll/pitch, D-DEFAULTS bandwidth transfer). Predicted RMS 4 deg/s.
- Alternatives: K_Y 15 (predicted 7.7, too close to 10); yaw-specific G5.1 limit (gate change, owner question,
  rejected: the airframe has the authority); yaw setpoint shaping (more code, F-9).
- Cost: yaw torque peak doubles on a 200 deg/s reversal (lowest motor 0.044 at hover 0.137 vs 0.083 at K_Y 10).
- Overturn: a G2 rate-yaw or attitude-yaw cell below GM 6 dB / PM 45 deg at K_Y 20; yaw saturation (motor at the
  lower limit) in G3/G5 runs that K_Y 10 did not saturate.

## D-A18-REOPEN (S140, 2026-11-20): G5.5 trajectory failure re-opens A18 (flatness jerk feed-forward)
- Evidence: G5.5 o1 s1 with matched GNSS (results/g5_g55_s140_gnss): estimate vs truth 0.05 m, but truth lags the
  setpoint by 160 ms (horiz RMS 0.78 m at zero shift, 0.47 m at best shift; limit 0.5); o2 0.93 m. Module runs
  `setFeedforward(false)` (McIndiPosControl.cpp:57): omega_ff = 0, so commanded acceleration is realised through the
  attitude loop (1/MC_ROLL_P 8 = 125 ms) plus rate/motor lag. Offboard jerk arrives finite 0, so the a_ref
  difference path is never used either. PID o1: 1.04 m (S139, mismatched GNSS), 185 ms lag.
- Decision: implement A18 as planned in D-outer-arch (jerk -> omega_ff side channel to the INDI rate module), with
  the jerk from the a_ref difference when the field is 0 or NaN in offboard; one-page design note first, two keys.
- Alternatives: raise MC_ROLL_P (shortens, does not remove the lag; stock tuning); lower the trajectory (weakens
  the test, rejected); accept the G5.5 fail (only if A18 shows no gain).
- Overturn: A18 on o1 gives < 0.1 m RMS gain (above the same-seed spread) or breaks a G5 mode edge.
- S141 outcome: A18 implemented (7e58bea57c). o1 s1 0.776 -> 0.590 m, o2 0.933 -> 0.793 m: gain > 0.1 m, kept. Rows still
  FAIL; residual lag 140 ms. Overturn of the G5.5 o1-o4/o7 limits is NOT considered; next: split the lag.

## D-A18-SOURCE (S143, 2026-11-20): G5.5 residual lag re-opens the A18 feed-forward model (drag), not the jerk source
- Evidence: results/g5_g55_s141_a18/lag_chain_s143.md (phase fit at w, self-test 100.1 ms on 100 ms): setpoint
  arrives undelayed (3 ms); a_c already lags the analytic accel 97/129 ms (large/small axis); attitude+thrust+plant
  add only ~20-40 ms. Truth fit a = 1.015 tilt_accel - 0.514 v (sim rotorDragCoefficient): the drag term is ~0.6 of
  the accel amplitude at w 0.85 and 90 deg out of phase. The flatness FF (a_ff, omega_ff = j/g) has no drag, so the
  stock vel/pos feedback carries it -> lag. omega_ff also misses d(drag)/dt = D*a (explains its misalignment).
- Route check 143 suggestion "runner sends trajectory jerk": not possible, MAVLink offboard has no jerk field.
- Decision: test the hypothesis first with one probe flight, firmware-free: runner adds D*v_ref to the sent accel
  (probe-only flag, never gate evidence). If o1 RMS drops by > 0.1 m: add a linear rotor-drag term to the module FF
  (a_ff + D v_ref, omega_ff from j + D a_ref; Faessler 2018), D a physical parameter identified from cruise data
  (body-xy specific force vs body velocity), default 0 = today's behaviour; INDI increment absorbs the residual.
- Alternatives: raise stock xy vel/pos gains (shortens, does not remove; tuning); trajectory jerk via uXRCE-DDS
  (does not fix the drag gap); accept FAIL with data.
- Overturn: probe gain < 0.1 m, or D identified from data differs from the truth fit by > 30 %.
- S143 outcome: probe results/g5_g55_s143_drag (o1 s1, D 0.514): horiz RMS 0.590 -> 1.111 m, overshoot (truth amplitude
  1.27/1.20): drag FF REJECTED (overturn met). Reading: the INDI increment already removes drag through the measured
  specific force; the drag-corrected stage delays of lag_chain_s143.md are therefore not trustworthy beyond "a_c lags".
  Per route check 143: lag chase STOPPED. G5.5 o1-o4/o7 recorded FAIL (probe) with data; the residual lag sits in the
  stock-PositionControl feedback that produces a_c (D-outer-arch base A, accel_only). Re-opening that is an
  architecture change: owner question only if G5.5 is still FAIL at the freeze re-fly.

## D-GAP-G510 (S150, 2026-11-21): G5.10 altitude-loss failure re-opens D-GAP (blend TB and bound), not the test
- Evidence (results/g5_g510_s148/s1, indi_pos_status read S150): after the 0.274 thrust drop the blend b rises
  0.016 / 0.113 / 0.243 at +0.25 / 0.75 / 1.25 s (LP with MC_INDI_POS_TB 1.0 s) and clamps at kMaxBlend 0.3 from
  +1.5 s to REC; altitude minimum at +1.7 s. Gap to absorb at hover: u_model 0.5 - mean_u 0.137 = 0.36 > 0.3, so the
  clamp also leaves a standing error (0.4 m low at REC). Until b catches up, the collective is carried by the stock
  z-loop error (a_c down to -17 m/s^2): lesson 9 in the thrust channel. THR_SC scales rotor speed (sqrt, on the
  outputs, GZMixingInterfaceESC.hpp:98), so mean_u sees the drop: a command/omega^2 gap, the D-GAP case.
- Candidates: (1) lower TB (faster DC restoration; limited by the outer acceleration-break margin, D-GAP risk of a
  lightly damped mode); (2) kMaxBlend sized to the largest gap the gates ask (G5.10: 0.36 at 2x hover, so >= 0.5);
  (3) D-GAP alternative (b), integrator on the acceleration error. (1)+(2) keep one mechanism and are tried first.
- Test: probe TB 0.3 s, seed 1 (results/g5_g510_s150). Accept (1) only with G2 outer-cell margin at the new TB.
- Overturn: TB 0.3 s still loses > 2.0 m, or costs the outer-break PM below 45 deg -> candidate (3), or owner Q9 (c).
- Physical floor: with a 0.033 s motor and ~0.1 s INDI response the ideal loss is ~0.1-0.3 m, so 2.0 m is reachable;
  the row is not failed by physics (PID loses > 3 m).
- S150 result: (2) done, kMaxBlend 0.5 (003e25c6d4, key2 MINOR: no negative-side test, deferred G7). (1) TB 0.3 probe
  s1 1.95 m at the old bound. Open: G2 outer-break margin at TB 0.3, then G5.10 3 seeds at TB 0.3 + bound 0.5.
- S151 outcome: ACCEPTED. Outer z accel-break PM 62.7 deg (r400) / 67.3 deg (r800), TB 1.0 ref 63.7 (results/g2_outer_tb03_s151, probe, unkeyed). G5.10 3 seeds alt loss 1.74-1.76 m, back 1.9-2.0 s (results/g5_g510_s151). Default MC_INDI_POS_TB 1.0 -> 0.3 (yaml + bench defaults). Overturn: a G5 re-fly at freeze that fails because of the faster blend (ramp/landing edge), or the keyed margin < 45 deg.
- S151 key2 ACCEPT (results/g5_g510_s151/key2_tb_default.md). xy at TB 0.3: PM 51.4 (vel/pos, S87 floor 49.7) / 65.2 deg,
  GM 16.8 dB. Cost: post-event transient larger than at 1.0 s (D-GAP: 0.107 vs 0.046 m), within G5 limits so far.
- S151 G5.4 probe at TB 0.3 (results/g5_g54_tb03_s151): edge 4.0/4.4 % hover, all limits PASS (= S135 at 1.0).

## D-PREFREEZE-R1 (S153, 2026-11-21): disposition of review r1 F2-F8 (design/prefreeze_r1_stage5.md)
- F2 (blend b reset at arm/disarm) -> SPEC AMENDMENT of D-GAP item 1: b starts at 0 at every arm, not only at boot.
  Reason: G5.9 (written S134, before any test) requires "re-arm: all INDI states zero"; a b learned on a previous
  flight is stale state of unknown validity (battery swap, payload change). Cost: a take-off with a gap carries it
  until LP_tb (0.3 s) absorbs it; the D-GAP check "land/re-take-off |b| within 10 %" applies without a disarm only.
  Alternative rejected: keep b across disarm (conflicts with G5.9). Overturn: a G3/G5 take-off with a weak motor or
  sag failing a G5.4 limit because of b = 0 at the edge.
- F3 (no lib reset on position-control re-entry / Hold exit) -> FIX: reset pending on the
  flag_multicopter_position_control_enabled rising edge and on the Hold -> run edge; held setpoint refreshed at
  re-entry. Overturn: G5.7 S->P / H->P transients worse than the S143 probe (3.6 deg, 3 % thrust step).
- F4 (dt clamp 0.04 makes "< 5 Hz -> hold" dead) -> FIX: true dt up to 0.2 s reaches the library; an interval
  > 0.2 s (rate < 5 Hz) holds, as D-STAGE-STALE (b) states. Alternative (delete the clause, require >= 25 Hz) rejected:
  leaves a silent wrong-dt band. Overturn: hold triggered in nominal SITL flights (interval jitter).
- F5, F6: comment fixes with the F3/F4 change. F7 (stock publish branch reachable while armed with pos/vel/climb all
  false) and F8 (G step HTE vs MPC_THR_HOVER at modelled-force edges): deferred to stage 7 with bound: G5.4 edge steps
  4.0/4.4 % (limit 10 %) include F8; F7 unreachable in any F-2 mode (offboard-accel sets vel). Reopen if a G5 edge
  step exceeds 7 % or a Bypass sample appears in an armed log.

## D-PREFREEZE-R2 (S154, 2026-11-21): disposition of review r2 (design/prefreeze_r2_stage3.md, opus, ACCEPT WITH FIXES)
- F1 MAJOR (INDI module start failure -> armable with no rate/pos controller, only a boot console error): accepted
  residual, same as stock PX4 (a failed mc_rate_control/mc_pos_control start is not refused by commander either);
  F-1 forbids the stock fallback and O-11 freezes commander. Stage 7: error tune + mavlink critical on start failure
  in rc.mc_apps, and a G8 bring-up checklist line ("check both INDI modules run before first arm"). Alternative
  (external arming-check registrant) rejected: needs a surviving module, more code than the risk. Overturn: a start
  failure seen in any SITL or board boot.
- F2-F4 MINOR (jerk-FF gate: fixed 50 ms age -> chatter if the outer loop runs 5-20 Hz; <= 50 ms FF tail after mode
  exit; publisher timestamp): deferred to stage 7. Bound: outer loop runs at 50 Hz nominal in every G5 flight; FF tail
  is inside G5.7 edge limits (3.6-3.7 deg PASS). Reopen if an indi_pos_status interval > 20 ms appears in a gate log.
- F5 MINOR (MC_INDI_ID_OK in-flight gain step; ID_OK 0 gives effective K_Y 10, the value that failed G5.1): freeze
  set flies G5.1 acro yaw also at firmware defaults (ID_OK 0), with the G2 firmware-default cell (STATE 4b).
- F6/F7 (no test for watchdog receipt stamp, rc.mc_apps matrix) and F8 (MC_INDI_POS_EN 1 with MC_INDI_EN 0 starts
  silently): stage 7, D-G7-HARNESS. S95 F4 (frozen-rpm gaps) stays deferred as before.

## D-PREFREEZE-R3 (S155, 2026-11-21): disposition of review r3 (design/prefreeze_r3_parity.md, sonnet checklist)
- 37 rows of module_parity.md: 0 OPEN, 0 SAFETY, 8 PARTIAL MINOR, 6 DEFERRED, 5 N/A, rest CLOSED. No opus key
  (RC154: key only on gaps). PARTIALs deferred to stage 7 with bounds: T2.frozen (one frozen ESC biases module B
  mean_u by <= 1/4 of its error, absorbed by the D-GAP blend; flown by the G3 frozen-telemetry draw), T1.5 (no INDI
  reset on a rates-enabled rising edge; G5.7 mode-edge rows PASS as probes), T3.11 (telemetry-loss warning only;
  O-5 modelled fallback by design), T1.8, T2.fresh. Reopen: a G3 frozen-telemetry or G5.7 failure tracing to them.

## D-FREEZE-6 (S155, 2026-11-21): stage-6 freeze definition
- Firmware: the commit pinned in the "Frozen at" line below (src/lib/indi_*, src/modules/mc_indi_*, gz_bridge). Any
  later firmware change: key2 only (RC154), then the G5/G2 rows it touches are re-flown; the change is logged here.
- Configuration: quad5in, bench/params/quad5in_indi_defaults.params with the runner overlay MC_INDI_ID_OK 1
  (run_scenario.py:1005) = "identified" set; nominal plant matched GNSS --gps-dly 110 --gnss-delay 110.
- Firmware-default cells added (D-PREFREEZE-R2 F5, STATE 4b, lesson 12): G5.1 acro yaw and G2 rate roll 800 Hz at
  ID_OK 0, W_MAX 0, ACT_TC 0.05 (the pre-identification state D-DEFAULTS-FW claims safe).
- Noise: GATES 5b requires the freeze re-fly with the G4 typical profile, so the re-fly waits for
  design/noise_profiles.md + a profile hook check (one pre-test flight); the text is not relaxed to sim default.
- Owner questions: Q8 (a)/(b)/add.2/add.3 and Q9 (a)/(c) scored at option A (recommended); an answer B re-scores or
  re-flies only the affected rows (G5.6, G5.8 3 m/s, G5.9a, G5.10, G5.11).
- Evidence: 3 seeds per row, serial (no parallel docker streams), each checker keyed before its verdict counts.
- Open anomalies touching the frozen code (A-1, A-6 outer loop; A-34/A-35/A-39 margins) stay open rows with
  their bounds; each is closed or re-bounded by the gate run that measures it (G4 for A-6, G2 for A-34-A-39).
- Frozen at: firmware 23acbdef67 (last commit under src/, S153); reviews r1-r3 dispositioned.
- Overturn: a gate row FAIL whose cause is in the frozen firmware -> one session of cause search, then re-open the
  decision underneath (owner rule), with a new freeze line.

## D-VIB-HOOK (S155, 2026-11-21, fixes A-49 before the G5 re-fly; implement S156, key2)
- Defect: per-rotor tones with offsets i*pi/2 cancel for equal rotor speeds; the IMU amplitude is unset and unknown.
- Choice (F-9 simplest calibrated): one tone pair referred to the IMU, as GATES 4 defines profiles: 1P at the mean
  rotor speed and blade-pass at N_b x 1P, amplitudes SIM_GZ_VIB_ACC / SIM_GZ_VIB_GYR = amplitude AT THE IMU at
  SIM_GZ_VIB_RPM (scaled by speed^2). N_b = 3 (design/ref_airframe_data.md:11, 3-blade 5.1 in prop), set by a SIM_GZ_ param
  (default 2 keeps x500 behaviour).
- Alternatives: seeded random per-rotor phases (amplitude still a beat, needs calibration per seed, rejected);
  per-rotor tones with spin direction (most physical, needs calibration and more code, rejected for now).
- Cost: no per-rotor beat / line width; one-line spectrum per harmonic. Overturn: a G4 metric or a G3 vibration
  failure that depends on the beat structure (then per-rotor model with measured net amplitude).
- Effect on the freeze: simulator change, not flight firmware; the G5 re-fly has not started, so no row is re-flown.
