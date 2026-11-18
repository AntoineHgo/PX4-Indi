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
     the measured mean_u at its limit are used). b starts at 0 at boot only. Recovery: when the freezing condition
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
