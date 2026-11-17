# Draft gates G3-G8 (T130, S64, DRAFT: not in GATES.md until the owner accepts)

Style as G1/G2/G2-STEP. Every number marked PROPOSED is mine (reasoning given) and for the orchestrator to accept or change.
No pass criterion is a ratio to PID (F-5); PID flies the same runs as reference only. Reference airframe quad5in
(0.610 kg, hover command 0.137, `design/ref_airframe_model.md`). Provenance G1.7 and the G1 evidence limits apply to every run.
Unverified here: scenario internals, metric scripts' exact outputs (only file names were listed), anything in C++.

## Shared definitions (PROPOSED, used by G3 and G5)
- **Loss of control (LOC)**, any of, evaluated on ground truth while airborne (landed == 0 and arm state armed):
  tilt > 60 deg for > 0.2 s (beyond any commanded tilt of the stack, MPC tilt limit 45 deg + 15 deg margin);
  or height below start-of-segment height by > 2.0 m unexpected (not in land/return descent); or ground contact
  (truth z at floor) while not commanded to land; or any NaN / controller `fault` flag; or horizontal excursion
  > 5 m from the reference at any time (4 x the gust-hold limit below). One LOC = run fails.
- **Sustained oscillation detector** (body rates p, q, r from truth, 800 Hz, uniform grid): Hann-windowed PSD in sliding
  windows of 4 s, step 1 s, in the band 2-40 Hz (above the outer loop, below the 0.4 x 100 Hz controller limit used in G2;
  motor chatter is G4). Flag a window when a single spectral peak has power > 20 x the median PSD of the band (peak
  prominence) AND window rate RMS at that peak > 5 deg/s; sustained = flagged in >= 3 consecutive windows, same
  frequency +-10 %. PROPOSED reasoning: 5 deg/s is below pilot perception but above the hover rate noise floor
  (to be measured, G4 pre-look); 3 s persistence excludes a gust or step transient. Also low band 0.2-2 Hz on position:
  peak-to-peak of detrended truth position > 0.3 m over 3 consecutive 10 s windows in hold = limit cycle.
  Existing near-matches: `bench/limit_cycle_check_s44.py`, `bench/motor_chatter_s44.py` (to be generalised; need a
  self-test with a known sine in noise, lesson G1.4).
- **Steady-state window** = last 10 s of a hold of >= 20 s after the last transient; truth, not EKF.

## G3 Robustness

Campaign: >= 300 runs after a pre-test of ~20 (pre-test checks every injector per G1.5, see prerequisites). Plant drawn
per run from a seeded sampler `bench/g3_sample.py` (MUST BUILD; seed -> JSON of plant + disturbance, logged in run.json).
Draw design: independent uniform per factor, log-uniform for multiplicative factors; 20 % of runs are corner runs
(each factor at an end of its range, 3-4 factors simultaneously) so extremes are not left to chance. PROPOSED.

| factor | range | form | exists |
|---|---|---|---|
| G1 / physical-parameter error | x[0.5, 2] on rotor-inertia/thrust-to-rate map used by the controller | mismatch via param (as `mismatch_inertia`, `mismatch_combined_*`) | partly: mismatch_* scenarios fixed values; sampler MUST BUILD |
| motor tau | x[0.5, 3], tau_down/tau_up in [1, 3] independent | `model_variant` (tau, tau_down) | tau2, asym exist; random draw MUST BUILD |
| added loop delay 0-10 ms | 0-10 ms in 1.25 ms steps | sim-side delay on the actuator or sensor path | NOT FOUND in scenarios.py: MUST BUILD (hook) |
| mass, inertia | +-30 % each, independently | model variant (SDF mass/inertia) | o6_zsine_mass, mismatch_inertia fixed; draw MUST BUILD |
| available thrust | 1.0-0.7: uniform sag and one weak motor | `thrust_sag`, `motor_fault` | exist (v2_sag_att, vp_sag75_att, vp_loss*, motor_loss_*); flown in attitude mode, need a position-mode variant |
| telemetry latency 0-3 frames | 0-3 | `SIM_GZ_ERPM_LAT` | `lat` (=2) exists; draw easy |
| telemetry loss / frozen | dropout 0-20 %, total loss 2 s, frozen 1 s | `SIM_GZ_ERPM_DRP`; total loss and frozen (`D-S3-FROZEN`) | drop exists; frozen and total-loss window MUST BUILD or confirm |
| vibration x[1, 5] | scale on IMU vibration noise | sim noise param | NOT FOUND: MUST BUILD (shares the noise hook with G4) |
| GNSS latency 80-250 ms, matched / mismatched EKF2_GPS_DELAY | latency + param mismatch +-100 ms | sim GNSS delay | NOT FOUND: MUST BUILD (hook) |
| wind and gusts | steady 0-5 m/s + gust 3 m/s (existing profile) up to 6 m/s peak | `gust_x`, `gust_diag` | exist but mis-sized (N1 C2): FIX FIRST |

Flight per run: `hover` + `step_roll` content + a `traj_lemniscate` segment in position mode, 90 s total (PROPOSED: one flight
covers hold, step and tracking so 300 runs cost ~300 x 90 s / speed 4 ~ 2 h sim wall, within budget). Mode: position, plus
20 % of runs in attitude and 10 % in acro-stick-free rate mode so the rate and outer loops are each exercised.

Pass (all per run; the gate fails on any, after every failure is explained and counted or excluded, below):
1. No LOC (definition above).
2. No sustained oscillation (detector above) on p, q, r and on position, over the whole flight.
3. Steady-state error in hold (truth, steady-state window), PROPOSED:
   horizontal RMS <= 0.15 m calm; <= 0.30 m with wind/gust; altitude mean error <= 0.10 m calm, <= 0.20 m with sag 0.7.
   Reasoning: EKF-truth height limit already 0.15 m (G1 limit 3), so truth limits cannot be tighter than ~0.15 m
   position; 0.30 m = a vehicle length x 1 at 3 m/s gust; `traj` RMS tracking error <= 0.5 m (lemniscate, hold excluded)
   because a 0.6 kg vehicle's footprint is ~0.25 m and obstacles are cleared by > 1 m in typical use.
   Attitude hold: roll/pitch mean error <= 1.0 deg calm (EKF heading error 1.6 deg yaw excluded: yaw limit 3 deg on estimate).
4. Recovery: after each injected event (gust, motor fault start) the return to within 0.3 m / 3 deg in <= 5 s.
5. Run is valid: <= 0.1 % holes (G1 limit 1), else re-fly (not a failure).
Campaign pass: 0 LOC, 0 sustained oscillation, items 3-4 met in >= 95 % of runs and every miss lists its cause
(PROPOSED: 300 runs with 0 failures bound the failure rate < 1 % at 95 % confidence (rule of three: 3/300); a 95 % item
quota applies only to steady-state accuracy limits, never to safety items). Failure treatment: a failure is excluded only
if the cause is a test defect (injector out of its G1.5-verified range, run-validity), proven on the log, and the
excluded count is <= 5 % of runs; physics-beyond-range (e.g. thrust < 0.7 with tau x3) is a limit, listed in the report.
Metric scripts: LOC and detector = MUST BUILD (`bench/g3_checks.py` + second key); tracking RMS from `bench/metrics.py` (exists).
Command (to be written): `bench/gate_g3.sh pretest|campaign N`.

## G4 Noise and effort

Profiles (MUST BUILD, none exists): quiet, typical, harsh = IMU gyro/accel noise density and bias, plus vibration lines
at motor frequency (~160 Hz at 999 rad/s hover = 159 Hz) and harmonics. Sources to record in `design/noise_profiles.md`:
PX4 flight-log review (public Flight Review logs of 5-inch-class and 250-class vehicles, raw `sensor_gyro` PSD),
datasheet of the IMU (ICM-42688-P type: gyro noise density 2.8 mdps/rtHz) for quiet; harsh = 99th-percentile
vibration in the logs. Every profile numeric (density, line freq, amplitude) with source line; no profile is accepted
without a recorded source (lesson 6). Sources not yet looked at: nothing here is verified.

Tests: hover 60 s and cruise (lemniscate `traj_lemniscate`, 5 m/s class) per profile, and acro stick-free hover
(`r_dot_f` pre-look listed in STATE NEXT). 3 profiles x 3 flights x 3 seeds = 27 runs. `hover` and `traj_lemniscate`
exist; noise profile selector MUST BUILD.

Pass (PROPOSED, true quantities from simulator truth, not the logged command):
1. True rotor-speed ripple: RMS of (omega_true minus 20 Hz low-pass, 20 Hz = above control bandwidth) <= 2 % of hover
   omega (~20 rad/s) typical, <= 4 % harsh, quiet <= 1 %. Reasoning: 2 % omega = 4 % thrust ripple, below the 5 % at
   which a 5-inch ESC/motor heating and audible whine show; to be adjusted after the first measurement since the PID
   reference value informs but does not decide (F-5).
2. Motor-command RMS (above the same 20 Hz cut-off, on the 0-1 command, D-EFFORT-BW fixed bandwidth): <= 0.02 absolute
   (2 % of full scale) typical, <= 0.04 harsh; peak command never saturates > 5 % of samples in hover. Reasoning: 0.02 of
   full scale at hover command 0.137 is ~15 % relative; beyond that the ESC current ripple exceeds the cell budget.
3. Cruise limits equal hover limits + 50 % (manoeuvre content), PROPOSED.
4. Attitude and position hold in hover on the harsh profile still meet G3 item 3 (noise must not buy accuracy loss).
Metric: `bench/a11_effort_rate.py` (effort at fixed bandwidth, exists) plus true-rotor-speed ripple from truth topics
(MUST BUILD or confirm `sim_ground_truth` carries omega); PSD via G3 detector. Prerequisite: G4 pre-look of `r_dot_f` noise.

## G5 Modes and transitions

All flown INDI stack, sim, quad5in, 3 seeds each unless stated; no scenario exists for any mode below except hover
(`hover`, position) and attitude steps, `traj_*` (offboard-style trajectory), `torque_steps`. Names to build:

| id | scenario (name) | test | transient limit PROPOSED (truth) |
|---|---|---|---|
| G5.1 | `m_stabilized`, `m_acro` | stick steps (roll, pitch, yaw) and release | stabilized: level within 3 deg in 1.0 s after release; acro: rate error <= 10 deg/s RMS on 100 deg/s steps; no LOC |
| G5.2 | `m_altitude`, `m_position` | step 2 m z, 3 m xy via stick | z overshoot <= 0.3 m, xy <= 0.5 m, settle 2 % in 4 s (3 m/s max speed, lemniscate class) |
| G5.3 | `m_hold`, `m_mission` | hold with wind; 4-waypoint mission | hold <= 0.3 m; waypoint reach 1.0 m acceptance, speed <= configured +10 % |
| G5.4 | `m_return`, `m_land`, `m_takeoff` | RTL from 20 m, land, take-off to 3 m | take-off: overshoot <= 0.5 m, no ground bounce; land: touchdown vertical speed <= 0.8 m/s, tilt <= 10 deg, no re-lift; RTL height error <= 1 m |
| G5.5 | `m_offboard` | existing trajectory scenarios `o1`-`o7` as offboard | G2 trajectory limits unchanged |
| G5.6 | `ev_false_maybe_landed` | inject maybe_landed true for 0.5 s at 3 m hover | altitude loss <= 0.3 m, attitude <= 10 deg, rate loop un-zeroed in <= 50 ms (D-S3-LANDED) |
| G5.7 | `ev_mode_switch` | switch position -> altitude -> stabilized -> hold during 3 m/s motion, 10 switches | each switch: setpoint step in thrust <= 20 % hover, attitude jump <= 5 deg, no LOC |
| G5.8 | `fs_rc_loss`, `fs_link_loss`, `fs_offboard_loss` | loss during motion | configured failsafe (hold/RTL/land) entered <= 1 s after the timeout, transient <= 1 m, then G5.3-5.4 limits |
| G5.9 | `ev_kill_rearm` | kill in flight (motors 0), re-arm on ground | motors 0 within 1 command period of kill; re-arm clean: integrator/state zero, no motor kick > 5 % at first 1 s |
| G5.10 | `ev_sat` | sustained saturation: thrust sag 0.6 for 5 s, then hover step, then recovery | no LOC, altitude loss <= 2.0 m, attitude <= 20 deg, no windup: recovery to 0.3 m in <= 5 s after saturation ends |
| G5.11 | `ev_est_reset` | EKF xy reset 1 m, z reset 0.5 m, yaw reset 5 deg during hold | position/attitude command jump <= 1 deg tilt, no oscillation after, truth excursion <= 0.5 m, rate loop sees no step |
Pass overall: every row no LOC, limits met on every seed. Existing support: `motor_fault`, `thrust_sag`; mode
injection by the scenario player (`D-SCHED`, sim-time mode changes: exists, used for G1.6); kill, failsafe, reset and
maybe_landed injectors = MUST BUILD (G1.5 check each before first use). Metrics: per-event window peak excursions from
truth around the logged transition (anchor on logged transition, G1 limit 2) = MUST BUILD (`bench/g5_events.py` + key).

## G6 Defaults and tuning method (checklist, short)
- Identification procedure script chain exists in part (`rate_fit.py` and the D-G1-DERIVE derivation); wrong start x2 and x0.5 on
  mass, inertia, tau, thrust constant; no manual tuning step (diff of params vs shipped defaults is only identified physics).
- Pass: G2 (all loops incl. outer), G3 campaign (>= 100 runs per start-error corner), G5 all rows, from each wrong start.
- Outlook (not pass): x500 (~1 kg), >5 kg; hover, steps, one trajectory, one gust, margins. Reported only.

## G7 Code and upstream (checklist)
- `git diff main -- src/modules/mc_rate_control src/modules/mc_att_control src/modules/mc_pos_control src/modules/control_allocator src/lib/control_allocation src/modules/commander` empty.
- Unit tests for both modules; each control behaviour has a test that fails when the behaviour is broken (break-checked, log it).
- Review items closed or justified (opus review deferred, STATE S58-S63); firmware defaults == validated parameter files (hash compare);
  `make format` and `make check_format` clean; flash/RAM on one NuttX board recorded (measured, not estimated);
  params/uORB follow `.github/instructions`; navigation terminology followed (AGENTS.md); clean firmware-only branch from `main`
  with no `indi_flight/` content.

## G8 Report (checklist)
Design first; validation per gate with evidence paths; limits (evidence limits of G1 + G3 excluded corners); hardware
bring-up checklist; errata and history appendix; `docs/en` page only (never ko/zh/uk).

## Prerequisites and defects to fix first
1. N1 C2: `disturbance.py` payload_add, com_shift, gust_x, gust_diag sized for x500; take mass/drag from the flown model, G1.5 check per profile.
2. Hooks: loop delay, GNSS latency, vibration scale, noise profiles, telemetry frozen/total loss (check), kill/reset/maybe_landed/RC-link failsafe injectors.
3. G3/G5 scenarios in position mode with thrust gap (N1 C3: motor_fault/thrust_sag are attitude-mode).
4. G1.5 check per injector before first campaign (deferred in G1 FINAL).
5. Noise-profile source note (G4), before any threshold is final.
6. Second keys for `g3_checks.py`, `g5_events.py`, ripple metric (lesson 1).
7. Hover command 0.137 with thrust ~ command^2 implies thrust/weight ~ 53 if taken literally: VERIFY the thrust-sag scale and "available thrust" definition against `ref_airframe_data.md` before G3 sizing (I did not).

## Build order for stage 5 (what the code must provide per G5 item)
1. G5.2/5.3 position/altitude/hold: INDI linear-acceleration loop in all position modes with the stock setpoint topics; the S60 hover slice is the base.
2. G5.4 take-off, land, RTL: use the stock navigator setpoints; landing needs the land-detector-driven thrust ramp and D-S3-LANDED.
3. G5.6 maybe_landed: rate loop must not zero thrust or integrators on maybe_landed, only on landed.
4. G5.7 mode switches: state hand-off (no step in thrust or attitude setpoint; first-sample reset of filters).
5. G5.8 failsafes: no INDI action needed besides valid setpoints; test that the loop survives setpoint timeout (D-S3-SPTO) and offboard loss.
6. G5.9 kill/re-arm: clear all INDI states at disarm, re-arm initialisation.
7. G5.10 saturation: anti-windup / thrust-priority allocation, outer-loop acceleration limit coupled to available thrust.
8. G5.11 estimator reset: on xy/z/yaw reset counters, shift the outer-loop references so the commanded acceleration does not jump.
9. G5.1 manual/acro: rate and attitude set points from sticks through the same INDI stack (A18 flatness not needed).
10. G5.5 offboard: accept position/velocity/acceleration setpoints with the flatness feed-forward (D-outer-arch).
