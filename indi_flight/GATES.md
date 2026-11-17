# Gates: exact tests and thresholds

Written before the first test of each gate and committed. After a gate's first test its thresholds change only to
fix a defect in the test, logged below the gate with date and reason. Starting values are the owner's (MISSION.md);
any tightening or change is justified in `DECISIONS.md`. PID flies the same tests as a reference, never as a pass
condition (F-5). All tests on the reference airframe (F-3) unless stated.

## G1 Evidence integrity (draft 2026-11-15, not yet tested)

Each item is one command (`indi_flight/bench/gate_g1.sh <item>`, to be written) and a pass rule.

| item | test | pass |
|---|---|---|
| G1.1 log rates | parse a nominal flight; for every topic an analysis script declares it needs, compare logged median sample period with the declared rate | every declared topic logged at >= the declared rate, max gap < 3 declared periods outside the start-up second |
| G1.2 ground truth | ground-truth pose carries the simulator's own pose time stamp (sim time), not reception time; check against a scripted constant-velocity truth segment | stamp offset vs sim time < 1 physics step; tracking metrics read truth, not the EKF |
| G1.3 two keys | every primary metric computed by two independently written scripts from the same raw logs | agreement within 1 % relative or 1 mm / 0.1 deg / 0.1 % FS absolute, whichever is larger, on the G1 sample set (>= 5 logs spanning hover, steps, trajectory, disturbance) |
| G1.4 self-tests | every metric and identification script has a synthetic test with a known answer, including one closed-loop case for each identification script | all pass in the bench test runner; each test checked once to fail when the script is broken (lesson 20) |
| G1.5 injectors and variants | each injector and plant variant flown once with the effect measured on the simulator side: frame (body vs world), units, application time in sim time vs commanded, effect on the measured rotor speed | frame and sign correct; magnitude within 2 %; applied time within 1 physics step of commanded and logged as applied |
| G1.6 determinism | same seed, plant and scenario flown 5 times at speed factor 1 and 5 times at the batch speed factor; hover, one step scenario, one trajectory; mode instants checked in the ULog (not the runner's HEARTBEAT view) | (a) PX4 mode transitions within 2 IMU periods across runs; (b) for every primary metric, same-seed spread (max-min) <= max(10 % of the threshold of the gate that uses it, the G1.3 absolute floor); (c) the cause of any remaining run-to-run difference is identified and its bound stated; (d) rule for every later verdict: a metric passes or separates two configurations only if its distance to the threshold (or the difference) exceeds the measured same-seed spread |

G1.1 declared-rate fix (2026-11-16, s20, test defect): the declared rates were a stale copy of the 4 ms world config, not the analysis need. Now: truth topics (position, attitude, angular velocity) at the controller rate (they score rate/attitude tracking); vehicle_local_position 88 Hz (EKF2 output 800/9 Hz on the 1.25 ms world, cause in `design/t39_g1_fixes_s20.md`; position estimator error is a separate metric, not a tracking score). Gap rule unchanged; truth rows FAIL on it (A-15).
G1.6 change before first test (2026-11-15, s13): relative 2 % target replaced by (a)-(d). Reason: hover metrics sit at the noise floor (max deviation 3-4 cm, attitude RMS 0.03 deg), where a relative spread is ill-conditioned (`design/determinism_s12.md`, `design/determinism_s13.md`). See DECISIONS.md D-G1.6.

G1 provisional verdicts (2026-11-16, s27, route check 27 item 1). PROVISIONAL: they assume the recommended option
of owner questions Q2 (A) and Q3 (A); no item is marked passed until the owner answers; reopened if the owner picks B or C.
Thresholds unchanged.
- G1.1 under Q2-A: (i) logger completeness sim_ground_truth 56578 vs gyro 56586 samples (-0.014 %, limit 0.1 %): met;
  (ii) sim holes 7 in 56586 steps (0.012 %, limit 0.05 %), single holes 5.0-6.3 ms (limit 10 ms): met (S24 numbers,
  hover speed 4; re-measure on the final G1 command).
- G1.6 under Q3-A (evidence `results/g16_sched_set_s26/speed4/README.md`; speed 1 pending): (a1) triggers at the same
  sim time within 1 IMU period: met (0 or +1250 us, 15/15). (a2) PX4 response spread 6.25-8.75 ms: within one
  Commander period; latency 1.25-10 ms (arm) and 11.25-20 ms (offboard), so the response is bounded at 2 Commander
  periods, not 1. (b) spreads recorded in `spread.json` (step_roll tighter than pre-player by 3-10x on timing
  metrics). (c) NOT MET: in 2/15 runs the EKF height is 2.3 m off before arm (A-14 reopened), so the flown hover
  altitude differs; cause not identified. (d) in force.

G1.6 verdict (2026-11-15, s17, evidence `results/det_g16_s4/`, `results/det_g16_s1/`, `results/det_g16_w125/README.md`,
second key `results/second_key_window_s15.md`): (a) NOT MET: mode-instant spread 7.5-11 ms on the 1.25 ms world
(threshold 2 IMU periods = 2.5 ms), 12-16 ms on the 4 ms world. (b) open until the G3/G5 thresholds exist; the
spreads are recorded in `spread.json` per batch. (c) MET: cause = mode commands sent over UDP into gz, which is not
lockstepped with PX4, so a command lands on a different IMU tick per run; tracking spreads of the same order with
the window anchored on the logged mode change (<30 % relative on non-floor metrics). (d) in force. Thresholds not
changed. Remedy candidates (stage 1, before G3): lockstep gz, or switch modes inside PX4 at a scheduled sim time.
Effort metric: raw derivative RMS is sample-rate dependent (A-11, closed s17), so G4 effort is defined at a fixed
bandwidth on a uniform grid.

G1 status (2026-11-16, s33). Thresholds unchanged; nothing marked passed (Q2, Q3, Q4 open).
- G1.1, G1.6(a): provisional under Q2-A/Q3-A as above. G1.2, G1.3, G1.4: met with two keys (second-key attitude
  angle fixed to the atan2 form, s33).
- G1.5: not tested; deferred per injector to G3/G5 if the owner accepts Q4-A.
- G1.6 re-fly with the baro fixes (`results/g16_set_s32/speed{4,1}/README.md`, 2 x 15 runs): spreads equal at speed
  1 and 4 (step delay <= 1.7 %, settle <= 1 IMU period, traj position <= 1.1 %, effort <= 2.5 %). (b) recorded,
  thresholds pending G3/G5. (c) remaining differences with known source and bound: Commander tick (Q3), EKF heading
  error A-19 (mechanism candidate s33: EKF2 declination vs sim field and mag-bias state; hover attitude spread
  0.86-0.93 deg), EKF-truth height A-14/A-20 (<= 0.174 m, 2/30 runs with 0.72 m initial baro bias). (d) in force.

## G1 FINAL (2026-11-16, s36): frozen with evidence limits, provisional under Q4-A

**Owner answers (2026-11-17, S50; Q2-Q4 closed, text in JOURNAL.md).** Q2: A amended (G1.1 = logger completeness,
every published sample logged, <= 0.1 % missing, against gyro/truth counts; holes per evidence limit 1 below).
Q3: A with the S27 wording ((a1) triggers at the same sim time within 1 IMU period; (a2) response spread <= one
Commander period 10 ms, latency <= 20 ms; windows anchor on the logged transition). Q4: A, G1 frozen with its
evidence limits; the "provisional" mark on G1.1, G1.6(a) and stage 2 is lifted. Added item G1.7 (below), required
before any G2 result counts. G1 counts as passed once G1.7 is implemented and its runner check is break-tested;
G1.5 stays deferred per injector as written.

| G1.7 provenance | a gate-bearing run records in run.json: commit, clean-tree flag, SITL binary hash (binary built from that commit), sim model file hashes, param file hashes; the runner refuses a gate-bearing run on a dirty tree or a binary not built from the recorded commit | runner refusal break-tested (dirty tree, stale binary) |

Thresholds above unchanged. G1 is frozen in the state below; it is NOT marked passed: the owner has not answered
Q2, Q3, Q4. If the owner answers Q4-B, every stage-2 result marked "provisional under Q4-A" is re-run after G1
passes in full; if Q2 or Q3 is answered B or C, G1.1 or G1.6(a) is reopened as written there.

| item | state | evidence |
|---|---|---|
| G1.1 | met under Q2-A (logger completeness -0.014 %, sim holes 0.012 % of steps, single holes <= 6.3 ms); fails the original gap rule on simulator holes (A-13) | S24 numbers, hover speed 4; re-measured on the first stage-2 batch with `bench/gate_g1.sh` |
| G1.2 | met (truth topic stamped in sim time, metrics read truth) | S21-S23, two keys |
| G1.3 | met (two keys, atan2 attitude angle in both) | S23, S33 |
| G1.4 | met (self-tests break-checked) | S28, S32 |
| G1.5 | deferred: each injector and plant variant gets its G1.5 check before its first campaign (G2 gyro injection, G3 variants, G5 events) | route check 30 |
| G1.6 | (a) under Q3-A: (a1) met, (a2) response spread within one Commander period, latency within two; (b) spreads recorded, thresholds set with G3/G5; (c) met with stated sources; (d) in force | `results/g16_set_s32/speed{4,1}/README.md`, `results/a20a19_s35/README.md` |

Evidence limits every later verdict carries:
1. Holes (amended by owner answer Q2, 2026-11-17 S50; the former global bound 0.05 % / 10 ms is withdrawn, it was
   already exceeded by S47 `measured_g2`). Two kinds, both reported per gate-bearing run: sim holes (gaps in
   `sensor_gyro` / `sim_ground_truth`) and controller holes (gaps in `vehicle_angular_velocity` / `actuator_motors`
   while `sensor_gyro` is continuous: a skipped rate-loop cycle). Every frequency-response or spectral window
   excludes both kinds, or shows its result unchanged without them. More than 0.1 % holes in a run -> re-fly that
   run (not a gate failure).
2. Commander tick (Q3): mode-change response spread <= 10 ms, latency <= 20 ms. Analysis windows anchor on the
   logged transition, never on the trigger.
3. EKF-truth height (A-14): <= 0.15 m in hover windows; position-hold spread <= +-0.15 m. Tracking scored on truth.
4. EKF heading error (A-19): |truth - EKF yaw| <= 1.6 deg, constant within a hover. Yaw verdicts are stated on the
   estimate, with the heading error reported beside them; no yaw threshold below 1.6 deg on truth.
5. Bench parameter sets carry SENS_BAR_AUTOCAL 0 (A-20) and the logger poll `-p actuator_motors` (S16).

## G2 Stability margins, measured (written S40 2026-11-16, before the first G2 test; provisional under Q4-A)
Thresholds are the owner's starting values (MISSION.md), unchanged. Results flown in stage 2 are preliminary; the
gate is decided on the frozen final pair in stage 6 with the same tests.
- **Loops and break points.** Rate roll, pitch, yaw: INDI at M3a (torque setpoint, D-G2-BREAK, D-G2-INJ), PID at M1
  (gyro) with M2 as cross-check. Attitude, velocity, position and the INDI acceleration loops: break points are
  specified in a design note with the same template (every feedback path the break cuts named, lesson S36) and
  second-keyed before their first flight; the thresholds below apply to them unchanged.
- **Configurations.** Reference airframe quad5in, controller rates 800 and 400 Hz (pass) and 267 Hz (reported; the
  nearest integer divisor of the 800 Hz IMU to the mission's 250 Hz, D-SIM-STEP). INDI in both actuator-state paths:
  model-only (no telemetry) and measured rotor speed (`--sim v2`), since F-1 requires the loop to hold without
  telemetry (O-5 fallback).
- **Excitation.** Schroeder multisine, 10 bins/decade, 1-60 Hz (FMAX <= 0.4 x controller rate), NP >= 3 periods with
  the first discarded, in hover. Amplitude: the smallest one whose coherence passes, chosen in a pre-test where two
  amplitudes (x1, x2) give |L| within 1 dB and arg L within 5 deg over the decade around crossover (linearity).
- **Estimator.** `bench/margins_est.py` (`frf_periodic`), self-tests 1-3 pass; frequency points kept only where
  coherence >= 0.8, and >= 0.9 within one decade of each crossover. A run whose crossover region lacks coherent
  points is invalid (re-fly), not a failure.
- **Validity of each run.** Over the injection window: `indi_rate_status` fault == 0 and landed == 0, u = c + d
  (max error <= 1e-6), logged rate = controller rate with no gap > 3 periods except sim holes (Q2) and the result
  unchanged when windows with a hole are left out; injected d equals the generator on `timestamp_sample`.
- **Pass (per loop, per configuration).** Gain margin >= 6 dB, phase margin >= 45 deg, delay margin >= 2 control
  periods + telemetry latency (model-only: + 0). Each margin is the worst of 2 runs (different seeds; the spread is
  reported as the estimator's repeatability, not as generalisation, lesson 5). GM is reported together with the
  minimum of 1/|L| over frequencies where arg L is within 10 deg of -180 deg; the pass uses the smaller of the two
  (phase plateau, T80).
- **Cross-check with the linear model** (`bench/margins_models.py`, same loop, same parameters): measured and model
  PM within 10 deg and GM within 3 dB, or the difference explained in `ANOMALIES.md` before the result is used. A
  margin that passes only because it disagrees with the model is not a pass.
- **Second key.** Margins recomputed from the same CSV windows by `bench/second_key_margins_s37.py`-style independent
  code (lesson 1); disagreement > 1 dB / 3 deg blocks the result.
- **One command per item:** to be named here when the G2 runner script exists (stage 2), before the gate run.

## G2-STEP Inner-loop attitude step criterion (written S61 2026-11-17, owner note N1 B.2, before its first test)
- Test: step_roll, step_pitch (15 deg), step_yaw (45 deg) on quad5in, sim v2 (eRPM), 800 Hz (400 Hz reported), speed 4,
  firmware INDI defaults + derived physical parameters only, >= 3 seeds, provenance G1.7 (clean tree, binary at HEAD).
  Command template: `results/stage3_s61/fly_steps.sh`; metrics (S63, replaces `results/indi_vs_pid/plot_compare.py`,
  whose fixed 2.0-5.0 s window predates the definition below): `python3 bench/g2_step_metrics.py OUT.json FLIGHT_DIR...`,
  second key `bench/t127_step_metrics_key.py` (est_g2/gt_g2 rows); AGREE 9/9 on S62 (`design/t128_g2_step_metrics_s63.md`).
- Pass, EVERY seed: roll and pitch overshoot <= 5 %, 2 % settle <= 450 ms; yaw overshoot <= 5 %, 2 % settle <= 1350 ms.
- Derivation (absolute thresholds, F-5: PID only informs the values; DECISIONS D-S3-ATT-STEP): PID reference S61 seeds
  1-3 roll/pitch overshoot 0 %, settle max 412 ms -> 412 x 1.1 = 453, rounded down to 450; yaw overshoot <= 0.3 %, settle
  max 1240 ms -> 1364, rounded down to 1350. Overshoot 5 % = owner's starting point (a 15 deg step overshoots by
  <= 0.75 deg). Tightening below 5 % not justified: the stock PID's 0 % is an overdamped tune, not a requirement.
- Also checked, not pass conditions: torque-step peak deviation reported next to the S61 INDI values (no regression of
  more than 10 % expected; a larger one is explained in the report).
- Measurement definition (written S63 2026-11-17, before the first test; closes A-28, evidence
  `results/stage3_s63/README.md`). Corrects two defects of the S61 text, no threshold changed:
  - t_on = first `vehicle_attitude_setpoint` sample whose step-axis angle has moved by >= 50 % of the step from its
    median over the 1 s before; never the runner's scheduled time (it lags 13-23 ms).
  - Window [t_on, t_next - 50 ms), t_next = the next setpoint crossing found the same way (return step); the S61 3.0 s
    window took in the return step of the 3.0 s roll/pitch hold (T127 seed3 roll 'exit at 2.96 s').
  - Pass metrics (overshoot, 2 % settle, rise 10-90 %) on the estimated attitude against the setpoint, as in S61: the
    controller's own loop. Also a pass condition (lesson 3): overshoot of the ground truth over the setpoint <= 5 %.
  - Reported apart, not pass conditions: truth settle against the setpoint, and the estimator error est - truth
    (mean over [t_on - 1 s, t_on) and over the last 1.5 s of the window). S62 and PID alike: roll/pitch est - truth
    grows from ~0 to +0.21-0.24 deg in 0.6-1.5 s after a 15 deg step (EKF tilt while accelerating sideways in
    attitude mode); yaw +0.6-1.0 deg standing bias. It is the same under PID, so it is the stock estimator's, not the
    controller's; the report states it next to the step results.
