# Gates G3-G8 final test text (S94 proposal, for paste into GATES.md)

Replaces `design/gates_g3_g8_draft_s64.md` after the S64 amendments (GATES.md lines 177-190). Tag on every number:
SOURCED (file or line cited) or PROPOSED (reason given). PID flies the same runs as a reference only (F-5): no
threshold is a ratio to PID. Reference airframe quad5in, 0.610 kg, hover thrust fraction 0.137 = (999/2700)^2, T/W 7.3
(GATES.md S64 amendments, SOURCED). Owner ranges (MISSION/owner definitions) are floors: a range may be widened or get
extra corners, never narrowed. Not checked in this note: C++ internals, `model_variant.py` internals, the public noise
sources (no web access used; G4 source note still to be written, lesson 6).

## 1. Hook table (state at HEAD 4542ca1d83)

Evidence: `design/g3_hooks_check_s65.md` (S65, read-only), re-checked now by grep of `gz_bridge/`, `bench/`, JOURNAL.md.
No hook was built after S65 (JOURNAL S65 "NEXT": build loop delay, GNSS sample delay, per-run drop seed, IMU noise scale
as one simulator task; no later entry reports it done; S82 injector = outer-loop accel break, unrelated).

| hook | state | where and how it is set |
|---|---|---|
| Added loop delay 0-10 ms | MISSING | No delay line on IMU, actuator or GNSS path in `GZBridge.cpp` / `GZMixingInterfaceESC.cpp`; only `ScheduleDelayed(10_ms)` at `GZBridge.cpp:201` (module scheduling). No scenario or CLI key. Needs a sim-side delay line, sim-time stamped, 1.25 ms steps. |
| Vibration scale x[1,5] | PARTIAL | Rotor-tied sinusoid on IMU 0: `GZBridge.cpp:623` `addRotorVibration` (called :681), params `SIM_GZ_VIB_ACC` (m/s^2, `module.yaml:145`), `SIM_GZ_VIB_GYR` (rad/s, :158), `SIM_GZ_VIB_RPM` (:170); needs `SIM_GZ_ESC_FB` 1 or 2; `reboot_required` (set before start, per run). CLI `--vib-acc/--vib-gyr` (`run_scenario.py:627-628,718`). Existing x3 point = 3.0 / 0.15 (`scenarios.py:166`), so x1 = 1.0 / 0.05. MISSING: wideband IMU noise scale (the SDF gaussian noise, gyro stddev 8.7e-4 rad/s, `sim/staged/quad5in_base_model_a14.sdf:186`, is fixed) and any profile selector (G4). |
| GNSS latency 80-250 ms | PARTIAL | Sample delay MISSING: the sample is stamped with current sim time (`GZBridge.cpp:972`; help text `run_scenario.py:630-631`: "gz GNSS has no latency but stamps no sample time"). The EKF-side compensation param EXISTS: `--gnss-delay` sets `SENS_GNSS0_DELAY` (`run_scenario.py:723`); the draft's name `EKF2_GPS_DELAY` is wrong (JOURNAL S65). Matched/mismatched needs the sample delay line plus this param. |
| Telemetry latency 0-3 frames | EXISTS | `SIM_GZ_ERPM_LAT` int 0-8, delay line `GZMixingInterfaceESC.cpp:161-163`, `module.yaml:116`, reboot_required; needs `SIM_GZ_ESC_FB=2` (v2 sim, `run_scenario.py:715`). Scenario `lat` = 2 (`scenarios.py:153`). |
| Telemetry dropout 0-20 % | PARTIAL | `SIM_GZ_ERPM_DRP` (`module.yaml:105`, `GZMixingInterfaceESC.cpp:151`, CLI `--erpm-drop`). The RNG seed is fixed in code (`GZMixingInterfaceESC.hpp:131`): repeatable, not per-run. Needs a seed param so G3 draws are independent. |
| Telemetry total loss / frozen | EXISTS | `SIM_GZ_ERPM_LOSS` bitmask, "held value, esc_errorcount increments" (`module.yaml:126`): total loss and frozen value are the same mechanism. Timed by scenario key `erpm_loss=dict(motor,start,end)` (`scenarios.py:164-165`, driver `run_scenario.py:857-878`). Needs a drawn start and 2 s / 1 s duration (draw only). |
| Battery sag (uniform) | PARTIAL | Scenario key `thrust_sag=dict(scale)`: runner ramps available thrust 1 to scale over the segment by writing `SIM_GZ_EC_*` (`run_scenario.py:860-864`, `scenarios.py:169,177`; thrust ~ omega^2 so scale s = sqrt(s) on command range, `scenarios.py:137`). Exists only for attitude-mode scenarios, and the runner refuses it under `--sched` (`run_scenario.py:669-671`): needs a position-mode scenario and a sim-time player kind (JOURNAL line 109). |
| Weak motor | PARTIAL | `motor_fault=dict(segment,motor|motors,thrust_scale)` (`scenarios.py:119,140,174-183`), same limits as sag (attitude mode, refused under `--sched`). Gap hook `s5_gap085/s5_loss08` exist (`scenarios.py:182-183`). |
| Motor tau, up/down asymmetry | EXISTS | `model_variant.py` (tau, tau_down) and variants tau2, asym (draft; `scenarios.py:V_PLANT`). Random draw = sampler only. |
| Mass, inertia +-30 % | PARTIAL | `model_variant.py` / `o6_zsine_mass`, `mismatch_inertia` fixed values; independent per-run draw = sampler only (model_variant internals not re-read). |
| G1 error per axis, controller vs plant | PARTIAL | `mismatch_*` scenarios with fixed values; needs a per-axis parameter file written by the sampler (controller G1 scaled, plant fixed, S64 amendment). |
| Wind, gusts | PARTIAL | `bench/disturbance.py` profiles `gust_x`, `gust_diag`, wind ramp, sized for quad5in in S65 (CdA 0.012 m^2, CoP 0.02 m UNVERIFIED), second key AGREE S66, A-31 (2x wrench) closed S67. Peak 9 m/s gives 0.595 N = 10 % W (`design/t132_disturbance_c2_s65.md`). Steady wind 0-5 m/s scaling needs a parameter. |
| Kill, re-arm, RC / link / offboard loss, estimator reset, false maybe_landed | MISSING | No injector named in `bench/`; G5. |

Order of build (cheapest first): per-run seed for drops; delay line (IMU/actuator) and GNSS delay line with one shared
sim-time stamped buffer; IMU noise scale; position-mode sag / weak-motor via sim-time player. Each gets a G1.5 check
(frame, units, applied time within 1 physics step, effect on measured rotor speed) before its first campaign run.

## 2. Shared definitions (G3, G4, G5)

- **Ground truth**: `sim_ground_truth` pose and angular velocity (G1.2: sim-time stamped, 800 Hz uniform grid); true rotor
  speed from the gz rotor joint speed (needs `SIM_GZ_ESC_FB>=1`; whether the log carries it is to be confirmed by G1.5,
  else add a truth topic). Never the EKF, never the logged command.
- **LOC** (any, airborne only, truth): tilt > 60 deg for > 0.2 s (45 deg stack limit + 15 deg margin, PROPOSED);
  height below segment start by > 2.0 m outside land/RTL; ground contact when not commanded; NaN or controller fault flag;
  horizontal excursion > 5 m from reference (PROPOSED: > 16 x the 0.3 m hold limit). One LOC fails the run.
- **Sustained oscillation** (PROPOSED, from draft; calibrate before first campaign): truth p, q, r on the uniform 800 Hz
  grid; Hann PSD, 4 s windows, 1 s step, band 2-40 Hz; window flagged when one peak has power > 20 x band median and the
  rate RMS at that peak > 5 deg/s (above the sim hover rate noise floor, measured by the G4 pre-look; below perception);
  sustained = flagged in >= 3 consecutive windows within +-10 % frequency. Position limit cycle: detrended truth position
  peak-to-peak > 0.3 m over 3 consecutive 10 s windows in hold. Self-test with a known sine in noise (G1.4, break-checked)
  at 4 deg/s (must not flag) and 8 deg/s (must flag). Near-matches to generalise: `bench/limit_cycle_check_s44.py`,
  `bench/motor_chatter_s44.py`.
- **Steady-state window**: last 10 s of a hold >= 20 s after the last transient, truth.
- **Run validity** (a failed validity is a re-fly, not a failure): holes <= 0.1 % (G1 limit 1); injectors applied within 1
  physics step of commanded and logged as applied; G1.6 rule (d) with the load floor if runs are parallel (GATES G1.6 S69).
- **Failure explanation** (every failure, no exception): record seed, sampler JSON, time of first violation, violated
  rule. Re-fly the same seed sequentially (reproduces? else test defect candidate). Restore each drawn factor to nominal one
  at a time and in the smallest subset that removes the failure: the cause is that subset. Classify: (a) test defect
  (proof on the log: injector outside its G1.5 range, hole, runner fault), excluded; (b) beyond-range physics (a limit
  stated in the G8 report, run stays counted); (c) controller defect: the gate fails until fixed and the campaign restarts
  from the pre-test. An unexplained failure fails the gate.

## 3. G3 Robustness campaign

**Design.** Pre-test 20 runs: each injector flown once at its extreme (G1.5), plus 5 sampled runs; the sampler, detectors and
checks are tested here and frozen. Campaign: >= 300 valid runs (owner floor, SOURCED), drawn by `bench/g3_sample.py SEED`
(to build; JSON of plant + disturbance stored in `run.json`). 240 runs: Latin-hypercube over the factors below, uniform
or log-uniform as noted (PROPOSED: stratification covers the box with fewer runs than independent draws). 60 runs (20 %,
PROPOSED) are corners: 3-4 factors simultaneously at an end of their range, from the named list C1-C6 below, 10 runs each.
Each run uses a distinct sampler seed and a gz seed from the sampler; the sampler seed list is committed with the result.

| factor | range (owner floor) | draw | note |
|---|---|---|---|
| G1 error, controller vs plant, per axis (roll, pitch, yaw independent) | x[0.5, 2] | log-uniform | S64: controller G1 / plant G1, not a rotor-inertia map |
| motor tau | x[0.5, 3] of nominal | log-uniform | |
| tau_down / tau_up | [1, 3] | log-uniform, plus 10 % of draws inverted [1/3, 1] | owner "asymmetry"; inverted added (widening) |
| added loop delay | 0-10 ms | uniform on 1.25 ms steps | MISSING hook; split 50 % actuator path, 50 % IMU path |
| mass | +-30 % | uniform | hover command scales with it |
| inertia (diag, independent of mass) | +-30 % each axis | uniform | |
| available thrust, uniform sag | 1.0-0.7 | uniform, in 40 % of runs; ramp over 10 s | at 0.7 and +30 % mass T/W is still 3.9 |
| weak motor | one motor 1.0-0.7 | uniform, in 30 % of runs | |
| saturation corner | available thrust down to 2.0 x hover thrust of the drawn mass (S64) | 10 % of runs (inside the corner set) | the only draw that saturates; scale about 0.27 on nominal mass |
| telemetry latency | 0-3 frames | uniform integer | |
| telemetry dropout / total loss / frozen | dropout 0-20 %; loss 2 s on one motor; frozen 1 s | dropout 40 %; loss 20 %; frozen 20 % of runs | start drawn inside the hold segments |
| vibration | x[1, 5] of the x1 point 1.0 m/s^2, 0.05 rad/s per rotor | log-uniform | x1 SOURCED `scenarios.py:166` / 3; G4 typical profile is added underneath |
| GNSS latency | 80-250 ms | uniform | MISSING hook |
| EKF GNSS delay param | matched (= latency) in 50 %; mismatched (latency + U[-100, +100] ms, min 0) in 50 % | | `SENS_GNSS0_DELAY` |
| wind | steady 0-5 m/s plus the existing gust profile, peak 3-9 m/s | uniform | direction uniform; 9 m/s peak = 10 % W (t132) |

Corners (PROPOSED, 10 runs each, every other factor drawn): C1 controller G1 x2 vs plant, tau x3, delay 10 ms (phase worst);
C2 controller G1 x0.5, mass +30 %, thrust 0.7, inertia +30 % (gain worst); C3 saturation corner 2.0 x hover, gust 9 m/s,
mass +30 %; C4 GNSS 250 ms mismatched -100 ms, wind 5 m/s plus gust, G1 x2; C5 vibration x5, telemetry frozen, dropout 20 %,
tau x0.5; C6 weak motor 0.7 on tau x3 and delay 10 ms. Signs of mismatch both ways are covered by C1/C2 and by the draw.

**Flight per run** (PROPOSED, 100 s sim): arm, take-off to 3 m; hover 25 s (window last 10 s); `step_roll` 15 deg sequence;
`traj_lemniscate` 30 s; hold 20 s (gust or fault injected at the start of the hold, window last 10 s). Modes: 70 % position,
20 % attitude (stabilized), 10 % rate with zero sticks (acro, owner "all modes" floor for the rate loop). Noise: G4 typical
profile always on. Cost: 300 x 100 s at speed 4 is about 2.1 h sim wall, one run per host slot (sequential rule, GATES G1.6).

**Pass per run** (all on truth; every threshold PROPOSED unless stated):
1. No LOC.
2. No sustained oscillation on p, q, r and on position, whole flight.
3. Steady-state (window above): horizontal RMS <= 0.15 m calm, <= 0.30 m with wind or gust; altitude |mean| <= 0.10 m
   calm, <= 0.20 m with sag or weak motor; roll/pitch |mean| <= 1.0 deg in attitude mode (yaw excluded: EKF heading
   error 0.6-1.6 deg, GATES G1 FINAL). Justification: 0.15 m is the EKF-truth height limit already accepted in G1, below
   it a truth limit is below the estimator; 0.30 m is half the 0.6 m prop-to-prop diagonal of a 5-inch frame (estimate, UNVERIFIED);
   1.0 deg lateral error is 1.7 % of weight drift.
4. Tracking: `traj_lemniscate` horizontal RMS <= 0.5 m and vertical RMS <= 0.3 m (owner: "within stated limits"); 0.5 m is about
   2 airframe lengths, the clearance a pilot needs at typical obstacle spacing (PROPOSED, see decision 3).
5. Recovery: after each injected event (gust, fault start) back within 0.3 m and 3 deg of the pre-event reference in <= 5 s
   and no re-excursion > 0.3 m for 5 s (five times the 1 s G2 settle scale, outer loop).
6. Rate mode (10 % of runs): body rate RMS <= 5 deg/s over the last 20 s with zero sticks (no oscillation, no drift in rate).

**Campaign pass**: 0 LOC, 0 sustained oscillation, items 3-6 met in >= 95 % of valid runs with each miss explained
(quota never applies to items 1-2). 300 valid runs with 0 safety failures bound the failure rate below 1 % at 95 %
(rule of three, SOURCED standard result). Excluded runs (class (a)) <= 5 % of the total, else the harness is not good enough.
Reported, not pass: per-factor sensitivity of items 3-5; PID on 60 of the same seeds.
Scripts: `bench/g3_sample.py`, `bench/g3_checks.py` (LOC, detector, steady-state) with a second key by a second writer
(G1.3), `bench/metrics.py` for tracking RMS (exists). Command: `bench/gate_g3.sh pretest | campaign N SEEDFILE`.

## 4. G4 Noise and effort

**Profiles** (to fix in `design/noise_profiles.md`, each number with a source line; none accepted without a source).
Structure PROPOSED: gyro and accel noise density, bias instability, and vibration lines at rotor frequency 159 Hz (999 rad/s
hover, SOURCED arithmetic) with blade-pass at 2x (2-blade prop) and one harmonic, amplitudes referred to the IMU.
- quiet: ICM-42688-P / IIM-42653 class datasheet: gyro noise density 2.8 mdps/rtHz (PX4 sim SDF already models IIM42653,
  stddev 8.7e-4 rad/s at 800 Hz, `quad5in_base_model_a14.sdf:186`; datasheet value from memory, to be re-read), rotor vibration amplitude x1 (1.0 m/s^2).
- typical: ICM-20602 / BMI270 class (higher density, datasheet to cite) plus a vibration line at the 50th percentile of
  public PX4 Flight Review / Betaflight blackbox logs of 5-inch quads (source note to write).
- harsh: 99th percentile vibration of the same logs; PX4's own log-analysis vibration classes if found in `docs/en/log/`
  (grep found no vibration thresholds in `docs/en/log/flight_review.md`: not available there).
No profile is built until the source note exists (owner: public sources). Selector = new hook (vibration + noise scale).

**Tests**: per profile, hover 60 s, cruise (`traj_lemniscate`, 5 m/s class as the draft; G3 speed is lower, PROPOSED), acro
stick-free hover 60 s; 3 profiles x 3 flights x 3 seeds = 27 runs (PROPOSED, a spread of 3 seeds is the G1.6 convention).
Acro needs the RC stick quantisation and sample-rate model before this row (S64 amendment): the `r_dot_f` path of the
stick sample (`bench/stick_profile.py` exists; the 50 Hz grid pacing from S82 is the base; quantisation step = 1/2048
of full stick, PROPOSED from the 11-bit SBUS channel resolution, to confirm).

**Metrics** (two cut-offs, S64 amendment, both reported; the pass limits sit on the 20 Hz one, the 4 Hz one has its own limit):
- R20 = RMS of (true rotor speed minus its 20 Hz low-pass), per motor, mean over motors, steady segments only (no steps).
- R4 = same with a 4 Hz low-pass (adds the control-band content: the part that is actuation, not noise).
- C20, C4 = same on the motor command (0-1 thrust fraction, `actuator_motors`) at fixed bandwidth on a uniform grid
  (`bench/a11_effort_rate.py`, D-EFFORT-BW, exists). 4th-order Butterworth zero-phase for both; filter edge 2 s excluded.
- Clip fraction = share of samples at command 0 or 1.
Pre-look floor (SOURCED, `results/stage3_s64/README.md` via GATES S64): quiet sim command HF RMS 2.7e-4, rpm HF RMS about 8 rpm
(0.1 % of hover).

**Pass** (true quantities from simulator truth; PROPOSED, Reasoning in the last column; confirm after the first measurement, never
adjusted to a PID value):

| quantity | quiet | typical | harsh | physical reason |
|---|---|---|---|---|
| R20, rotor speed ripple | <= 1.0 % hover (10 rad/s) | <= 1.5 % (15 rad/s) | <= 3 % (30 rad/s) | thrust ripple = 2 x speed ripple: 3 % thrust RMS on a 0.6 kg craft is 0.3 m/s^2 of acceleration noise (0.03 g) |
| C20, command RMS | <= 0.004 | <= 0.006 | <= 0.012 | 0.006 / 0.137 = 4.4 % of hover thrust, 2.2 % of speed: ESC and motor current ripple stays below 5 % of mean current |
| R4 | <= 3 % hover | <= 4 % | <= 6 % | 4-20 Hz is the control band; ripple here is actuation of real disturbance, so looser |
| clip fraction | 0 | 0 | <= 0.1 % | command 0 at hover 0.137 is 3 sigma of C20 harsh (0.036) with margin; clipping means lost control authority |
| cruise (R20, C20) | hover limit x1.5 | | | manoeuvre content; PROPOSED |
Additional: G3 items 1-3 hold on the harsh profile in hover (noise must not buy accuracy loss); no sustained oscillation by
the G3 detector, also on the command (band 20-100 Hz, peak > 20 x median, `motor_chatter_s44.py` generalised). Failure explanation as in section 2.
Command: `bench/gate_g4.sh profile flight seed`; scripts: `bench/g4_ripple.py` (to build, second key), `a11_effort_rate.py`.

## 5. G5 Modes and transitions

3 seeds per row, INDI stack, sim, quad5in, noise = typical profile; pass: no LOC and every limit on every seed; ground-truth
metrics around the logged transition (window anchored on the logged mode change, G1.6 rule). No scenario exists for rows
below except `hover`, attitude steps, `traj_*` and `torque_steps` (SOURCED draft); names are placeholders. Limits are PROPOSED.

| id | scenario | test | limit, truth |
|---|---|---|---|
| G5.1 | m_stabilized, m_acro | stick steps roll, pitch, yaw, release (stick model with quantisation, see G4) | stabilized: level within 3 deg 1.0 s after release; acro: rate error RMS <= 10 deg/s on 100 deg/s steps (about 10 % of the step) |
| G5.2 | m_altitude, m_position | 2 m z step, 3 m xy step by stick, 3 m/s | z overshoot <= 0.3 m, xy <= 0.5 m, 2 % settle <= 4 s |
| G5.3 | m_hold, m_mission | hold in steady 5 m/s wind with gust; 4-waypoint mission | hold RMS <= 0.3 m; waypoint 1.0 m acceptance reached; speed <= configured + 10 % |
| G5.4 | m_takeoff, m_land, m_return | take-off to 3 m; RTL from 20 m; land | take-off overshoot <= 0.5 m, no bounce; touchdown vertical speed <= 0.8 m/s, tilt <= 10 deg, no re-lift (land-detector transitions logged); RTL height error <= 1 m |
| G5.5 | m_offboard | `o1`-`o7` offboard | G2 trajectory limits unchanged (SOURCED GATES G2) |
| G5.6 | ev_false_maybe_landed | inject maybe_landed true 0.5 s at 3 m hover, also at 1 m during land | altitude loss <= 0.3 m, tilt <= 10 deg, rate loop active again <= 50 ms after release (D-S3-LANDED) |
| G5.7 | ev_mode_switch | position, altitude, stabilized, hold during 3 m/s motion, 10 switches | thrust setpoint step <= 20 % of hover, attitude jump <= 5 deg, no LOC |
| G5.8 | fs_rc_loss, fs_link_loss, fs_offboard_loss | each at 3 m/s and at hover | configured failsafe (hold, RTL or land) entered <= 1 s after its timeout, excursion <= 1 m, then rows G5.3-G5.4 limits |
| G5.9 | ev_kill_rearm | kill in flight, re-arm on ground, take off | motors 0 within one command period; re-arm: all INDI states zero (log), first-second motor command change <= 5 % of full scale, take-off passes G5.4 |
| G5.10 | ev_sat | sustained saturation: available thrust 2.0 x hover (about 0.27 of nominal, S64) for 5 s with a position step, plus a full-scale aggressive manoeuvre that saturates at full scale | no LOC, altitude loss <= 2.0 m, tilt <= 20 deg, no windup: back within 0.3 m in <= 5 s after saturation ends |
| G5.11 | ev_est_reset | EKF xy reset 1 m, z 0.5 m, yaw 5 deg during hold | tilt command jump <= 1 deg, no oscillation after (G3 detector), truth excursion <= 0.5 m |
Row G5.6 justification: 50 ms is about 5 x the 10 ms Commander period, one lost tick plus propagation (SOURCED G1 evidence, latency
bounded at 2 Commander periods). The 0.8 m/s touchdown limit is the usual soft-touchdown figure for a 0.6 kg craft
(PROPOSED). Injectors for kill, reset, maybe_landed, RC / link / offboard loss, position-mode sag, are MISSING and each needs
its G1.5 check first. Scripts: `bench/g5_events.py` (to build, second key). Command: `bench/gate_g5.sh row seed`.

## 6. G6 Defaults and identification from a wrong start

Procedure (fixed before the first test): start from physical parameters wrong by x2 and x0.5 each on mass, inertia, motor
tau and thrust constant (8 single-parameter starts plus the 2 all-high / all-low corners = 10 starts, PROPOSED); run the shipped
identification chain once (hover, steps; `rate_fit.py`, D-G1-DERIVE derivation); load the identified parameters; no other edit.
"No manual tuning" is checked mechanically: the parameter diff against the shipped defaults file contains only identified
physical quantities (script lists any other changed name; any one fails). Pass: from each start, G2 (all loops incl. outer),
G3 campaign of >= 100 runs per start-error corner (all-high and all-low; single-parameter starts get the 20-run pre-test set,
PROPOSED: 300 x 10 would be 3000 runs for no added information, the corner starts bound the others) and G5 all rows.
Failure: the identification does not converge in its fixed time budget, or any gate rule fails. Reported only: x500 (~1 kg)
and a > 5 kg vehicle, hover, steps, one trajectory, one gust, margins. Command: `bench/gate_g6.sh start_id`.

## 7. G7 Code (testable parts)

Each as a command with pass rule: (a) `git diff main -- src/modules/mc_rate_control src/modules/mc_att_control
src/modules/mc_pos_control src/modules/control_allocator src/lib/control_allocation src/modules/commander` empty (draft; confirm the
actual module names of the INDI branch, not verified here); (b) unit tests built and passing, each behaviour test fails when the
behaviour is broken (break-check logged); (c) hash of firmware default params == validated parameter files; (d) `make format`
then `make check_format` clean; (e) flash and RAM of one NuttX board measured from the build `size` output, recorded (no estimate);
(f) `.github/instructions` and navigation-terminology rules followed (reviewer checklist, not scripted); (g) the firmware-only branch
from `main` contains no `indi_flight/` path (`git diff --stat main -- indi_flight` empty). Not testable by gate: opus review items
(S58-S63) are a closed-or-justified list.

## 8. G8 Report (testable parts)

Checks: every gate section has an evidence path that exists; G1 evidence limits and G3 excluded corners (beyond-range list) listed;
hardware bring-up checklist present; errata and history appendix present; `git diff main -- docs/ko docs/zh docs/uk` empty;
page lives in `docs/en` only; markdown lint passes if `make` docs target exists (unverified). Command: `bench/gate_g8.sh`.

## 9. Decisions the orchestrator must make

1. Vibration base. x1 = 1.0 m/s^2 / 0.05 rad/s per rotor is only the existing V5 point divided by 3, not a source. Recommend:
   accept for G3 now, replace by the G4 typical profile once `noise_profiles.md` has sources.
2. Build or narrow loop delay and GNSS latency hooks. Recommend: build both (one shared sim-time delay line), they are owner floors.
3. Tracking and steady-state limits (0.15 / 0.30 m, lemniscate 0.5 m / 0.3 m, 1.0 deg) are estimator-floor and clearance arguments,
   not measured. Recommend: freeze after the 20-run pre-test using the larger of the proposal and the measured same-seed spread (G1.6 rule d), owner to confirm.
4. G4 limits (R20 1.0 / 1.5 / 3 %, C20 0.004 / 0.006 / 0.012) have no source beyond the thrust-ripple argument. Recommend: keep as
   targets, finalise after the first quiet and typical measurement; the harsh limit may only be loosened with a written physical reason.
5. G3 fraction of corners (20 %) and quota (95 % for accuracy items). Recommend: keep; safety items stay at 0 failures.
6. G6 sample size: 100 runs at two corner starts plus pre-test sets for the other 8 starts. Recommend: accept; the owner text says
   "pass G3" without a count, so a smaller G3 per start needs the owner.
7. Acro stick model: quantisation and rate for G4/G5.1. Recommend: model the 11-bit, 50 Hz case plus one coarse case (8-bit, 25 Hz) as a G4 sensitivity.
8. Whether a failure class (b) "beyond-range physics" run counts toward the 300 (recommend yes) and whether thrust 0.7 with tau x3
   and delay 10 ms is allowed to fail (recommend: it is in the owner range, so it may not; list it as a corner C6 and require a pass).
