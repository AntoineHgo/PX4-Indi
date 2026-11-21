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
G1.6 protocol clarification (2026-11-18, s69, test-protocol defect, thresholds unchanged): the G1.6 runs are flown strictly sequentially on an otherwise idle host, as in S32. Evidence: the G1.6 command at HEAD gives rise span <= 1.5 ms sequentially and ~11 ms (bimodal) with 5 concurrent runs (`results/a32_load_s69/README.md`). A parallel batch (G3) carries the measured load floor as its same-seed spread, stated with the result.

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

**G1 PASSED (S84, 2026-11-18)** under the owner's S50 rule above: G1.7 implemented (S50, `bench/provenance.py`,
`run_scenario.py --gate`), runner refusal break-tested, self-test `bench/tests/test_provenance.py` re-run S84: ALL PASS
(dirty tree, stale binary, header newer, missing input/binary refused). Carried with the passed gate: G1.5 deferred
per injector (each injector/plant variant checked before its first campaign), the five evidence limits below, and
a per-run hole reporter (evidence limit 1: sim vs controller holes) that must exist before any G2 cell counts.
Historical note (S36, superseded by the line above): G1 is frozen in the state below; it is NOT marked passed: the owner has not answered
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
- **Cell table (S84, route check 84).** Every cell is flown on the frozen pair in stage 6 with `--gate` (G1.7); the
  status column tracks preliminary (pre-freeze) evidence only. Rates: 800 / 400 pass, 267 reported. Paths: INDI
  measured (v2) and model-only; PID reference.

  Status updated S108 from existing results only (verdict note `design/g2_verdict_s108.md`; S84 status in git
  history). "keyed" = margins recomputed by independent code; "x-check" = linear model within 10 deg / 3 dB.

  | loop | break point | INDI injector | status (S108, preliminary, pre-freeze) |
  |---|---|---|---|
  | rate roll/pitch (16 cells, 800/400, v2 + model-only) | M3a torque setpoint (PID: M1 gyro) | MC_INDI_INJ_* (D-G2-INJ) | all PASS, 2 seeds, keyed (K100/K101); x-check YES, worst dPM 4.7 deg, dGM 1.86 dB (S105) |
  | rate yaw (8 cells) | M3a | MC_INDI_INJ_* | all PASS, worst GM 15.5 dB (meas. 400 Hz); x-check model-only 4/4 YES, measured-torque 1/4 (A-39: 400 Hz dGM -9.1/-9.7 dB) |
  | attitude roll/pitch/yaw (6 cells, 800/400) | attitude-loop output (rate setpoint) | MC_INDI_INJ_PT 1 | all PASS at HEAD (S107), PM >= 56.8 deg, GM >= 22.0 dB; ONE seed (gate asks 2); x-check PM YES (T195), GM model 3.4/4.6 dB low at 400/267 (A-36); yaw unmodelled |
  | INDI acceleration z, xy | stage output t_c (MC_INDI_PINJ_PT 1) | T174 S84 | z 4 cells PM 58.3-63.7 (S86/S88); xy 8 cells PM 60.9-64.8, GM 18.6-19.3 dB (S87); 2 seeds; margins NOT keyed (T183 keyed the xy FRF of 1 cell); no x-check |
  | velocity/position z, xy | stage input a_ref (MC_INDI_PINJ_PT 0, D-G2-PINJ) | done S82 | z 4 cells PM 57.3-66.1 (S83/S86); xy 8 cells PM 49.7-61.8, GM 18.2-18.8 dB (S87), seed spread up to 7 deg; margins NOT keyed beyond T183 (1 cell); no x-check |
  | 267 Hz (reported) | all | - | not measured at HEAD (S91 attitude roll cell failed hole check) |
  | PID reference | M1 gyro | not built (S102) | none, deferred (RC103) |
  | hole reporter | evidence limit 1 per run | `bench/hole_report.py` | DONE, frozen S89 (D-HOLE-FREEZE) |

  Before the stage-6 gate run: margin second key for the outer cells, linear outer-loop model, A-36 and A-39
  explained or bounded, 2 seeds everywhere, 267 Hz rows, serial flights only (S86 finding 1). No G2 closure claimed.

  Freeze status (stage 6, D-FREEZE-6 plant, serial, hole-checked; S160-S163):
  - rate roll/pitch/yaw x 800/400 x measured/model-only (2-3 seeds) + fwdef roll 800: all PASS, KEYED
    (results/g2_freeze_s160/README.md). Open: linear-model x-check at freeze params, phase-plateau GM rule.
  - attitude roll/pitch/yaw 800/400: 12/12 PASS, KEYED (results/g2_att_freeze_s162). Open: yaw model x-check.
  - vel/pos and accel x/y/z, 800/400, 2 seeds: 24/24 meet thresholds, KEYED S164 (results/g2_outer_freeze_s163,
    key2.md: 22/24 within 3 deg/1 dB, 2 z-accel cells differ on a crossing in a -27 dB notch, reported at the smaller
    GM 19.7 dB). Model x-check S164 (xcheck.md, bench/g2_outer_model_s164.py): PM 8/8 within 10 deg; xy GM model
    ~5 dB conservative (A-50, verdict independent); z no crossing in either. 267 Hz rows not flown.
  - Phase-plateau GM (S164, results/g2_plateau_s164.md, `python3 indi_flight/bench/g2_plateau_gm_s164.py`): 67 cells;
    literal rule 66/67, att ax2_r800_s2 hit by a 0.2 Hz bin with |L| > 1 (gain-reduction margin 18.5 dB). Defect fix
    proposed in Q13 (plateau over |L| < 1, reduction margin >= 6 dB reported); under it 67/67 PASS. Pending owner.

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
- **First test (S64 2026-11-17, HEAD 360c9ae453, clean tree): 9/9 PASS at 800 Hz**, seeds 1-3; second key AGREES on
  every pass metric (`results/g2_step_s64/README.md`). Roll/pitch OS 0.64-1.29 %, settle 341-366 ms; yaw OS 0.18-0.37 %,
  settle 913-923 ms; truth OS <= 1.29 %. Torque-step rejection not regressed. 400 Hz reported (S64, `results/g2_step_s64_400/README.md`): 9/9 within
  the same limits, roll/pitch OS 0.40-1.78 %, settle 312-360 ms; larger seed spread (A-30).

## G3-G8 test text, S64 amendments (superseded by G3-G8 FINAL S94 below, kept as history)
Draft: `design/gates_g3_g8_draft_s64.md` (T130, sonnet, every number PROPOSED). Each gate's section here is finalised,
with its numbers, before that gate's first pre-test; until then the draft is the stage-5 acceptance target. Orchestrator
review S64, amendments that override the draft:
- Draft item 7 resolved: command is thrust fraction (THR_MDL_FAC 1 inverts thrust ~ w^2), hover thrust fraction 0.137 = (999/2700)^2, so thrust/weight = 7.3, not 53. Consequence: "available thrust
  0.7" (G3) and "sag 0.6" (G5.10) leave 5x hover thrust and do not saturate anything on this airframe. G3 keeps the
  owner's 1.0-0.7 range (owner value) and ADDS a saturation corner sized on hover: available thrust down to 2.0 x hover
  (scale 0.27); G5.10 is sized the same way (scale ~0.2, T/W ~1.5) plus an aggressive manoeuvre that saturates at full scale.
- G3 G1-error factor = controller G1 (control effectiveness) vs plant, x[0.5, 2] per axis, not a rotor-inertia map.
- G4 metric reported on two cut-offs (4 Hz and 20 Hz) until the noise-profile sources fix the band; the S64 pre-look
  (`results/stage3_s64/README.md`) gives the quiet-sim floor: motor command HF RMS 2.7e-4, rpm HF RMS ~8 rpm (0.1 % of hover).
- G4 acro case needs an RC stick quantisation/sample-rate model (r_dot_f path, S64 pre-look) before r_dot_f in acro is closed.
- Hooks marked NOT FOUND (loop delay, GNSS latency, vibration scale) are to be checked against stage-1 simulator work
  (STATE/JOURNAL, `sim_review.md`) before being built: the draft read only `scenarios.py`.

## G3-G8 FINAL (S94 2026-11-18, before any first test of G3-G8)
Source: `design/gates_g3_g8_final_s94.md` (T197, sonnet; hook table in its section 1, PROPOSED/SOURCED tags kept).
S64 amendments are incorporated. Changes after a gate's first test only fix a test defect, logged here.

### Orchestrator decisions S94 (override the text below where they differ)
1. Vibration x1 point (V5/3) is provisional; it is replaced by the G4 typical profile once `noise_profiles.md` has
   sources, before the G3 pre-test.
2. Loop delay (0-10 ms) and GNSS latency (80-250 ms) are owner floors: one shared sim-time delay line is built
   (simulator hook: G1.5 check and second key) before the G3 pre-test. The ranges are not narrowed.
3. G3 items 3-5 thresholds are frozen now as written; the pre-test checks the set-up only. If its same-seed spread
   exceeds 1/3 of a limit, the limit is not changed here: owner question (gate change). The "half the prop diagonal"
   justification of 0.30 m is struck (wrong for a 5-inch frame, motor diagonal ~0.22 m); 0.30 m stays PROPOSED as
   twice the calm limit under wind.
4. G4 limits are finalised from the noise-profile sources before the first G4 measurement, never from an INDI result.
5. No quota: the "95 % of valid runs" rule for items 3-6 is removed. Every miss in a valid run is a failure, explained
   per the failure rule. Corners stay 20 % of runs.
6. Class (b) "beyond-range physics" applies only to draws outside the owner ranges (inverted asymmetry, saturation
   corner, gust peak above the owner text). Inside the owner ranges a failure counts; corner C6 must pass.
7. G6: identification from all 10 wrong starts must converge within the stage-4 tolerance; G2 and G5 are flown on the
   identified sets of the two worst-converged starts; the full G3 campaign (>= 300 runs) is flown on the worst-converged
   set, plus a 20-run pre-test set on each other start. Overturned if the owner reads "pass G3" as a full campaign per start.
8. Acro stick model: 11-bit / 50 Hz, plus 8-bit / 25 Hz as a G4 sensitivity (accepted as proposed).

### 2. Shared definitions (G3, G4, G5)

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

### 3. G3 Robustness campaign

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

### 4. G4 Noise and effort

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

### 5. G5 Modes and transitions

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
S144 G5.8 measurement definition (written before the row's first test, A-47, results/g5_events_s144/a47.md): the timeout
reference is the firmware's own time, not the runner's: link loss = last telemetry_status with heartbeat_type_gcs=1 +
COM_DL_LOSS_T (stock commander re-stamps the heartbeat up to 2.5 s after the last one); RC loss = flag rise of
manual_control_signal_lost minus COM_RC_LOSS_T 0.5 s; failsafe entry read from vehicle_status nav_state (published on
change), not from failsafe_flags (logged at 2 Hz). The 1 s limit is unchanged.
S145 test-defect fixes (first scoring S145, results/g5_events_s145/README.md; limits unchanged): G5.9 "INDI states"
= quantities carrying memory from the previous flight that are not re-derived from current measurements (increments,
integrators, gap remover, held commands); filtered measurements must track their input and are reported, not zeroed.
G5.9 "motors 0" is read on actuator_outputs (output stage), referenced to manual_control_switches.kill_switch. Event
timing topics (vehicle_status, failsafe_flags, telemetry_status, actuator_outputs) must be logged at every publication;
a verdict whose margin is below the logged period is not counted.
S131 addition to G5.4 (written before its first test; S131 AUTO smokes are probes, RC113): take-off handover, at the
`takeoff_status` rampup -> flight edge, |thrust command step| (`indi_pos_status.thrust`, mean 0.1 s after minus mean
0.1 s before) <= 10 % of the hover thrust, and truth altitude dip <= 0.3 m within 1 s after the edge. Land: mean truth
vz over the final descent within +-20 % of MPC_LAND_SPEED; disarm <= COM_DISARM_LAND + 1 s after ground contact. The
10 % is half the G5.7 mode-switch limit, since the handover is a scheduled, not pilot-commanded, edge (PROPOSED).

#### 5b. G5 FINAL (S134 2026-11-20, owner directive F-7/F-8/F-9; before the first G5 test; overrides 5 where they differ)
- Stack: quad5in, `MC_RATE_CTL_TYPE 1` + `MC_INDI_POS_EN 1`; a run is valid only if `indi_pos_status` exists and no
  `mc_pos_control` task runs. 3 seeds per row. Limits of section 5 become FINAL as written (absolute, truth); PROPOSED
  tags on them are removed. Noise: sim default until the G4 typical profile exists; the stage-6 freeze re-flies all
  rows with it (G5 batches before the freeze are probes, RC113).
- G5.4 take-off (F-7, one controller from arming): over the whole ramp and at the rampup -> flight edge,
  |mean `vehicle_thrust_setpoint` collective 0.1 s after - 0.1 s before| <= 10 % of hover, checked at the edge and at
  every 0.1 s step of the ramp after the first 0.5 s (the ramp itself climbs from 0 to hover in that time by design);
  truth dip <= 0.3 m within 1 s after the edge. Thrust signal is `vehicle_thrust_setpoint`, not `indi_pos_status`
  (logger misses its first ~0.2 s, S132).
- Not tested, owner decision F-8: accel-only offboard; take-off on an offboard setpoint alone (code path unchanged).
- Row -> scenario (F-9: existing first; a new injector only where the row cannot run without it, reason given):
  G5.1 attitude/rate steps in stabilized/acro (exist); G5.2 altctl/posctl stick steps (runner modes exist; a stick
  step segment only if missing); G5.3 `auto_tour`, `gust_x` in hold; G5.4 `auto_tour` take-off, `auto_land10`, RTL
  (runner AUTO harness S131); G5.5 `offb_vel_step`, `o1`-`o7`; G5.7 RC override mode switches (runner); G5.6, G5.8,
  G5.9, G5.10, G5.11: injector to build (maybe_landed, link/RC loss, kill, sat, EKF reset do not exist), each
  G1.5-checked before use. First batch = rows with existing scenarios.
- G5.1 exact test (S136, before its first test; the row did not state step amplitude, timing or the RMS window).
  Scenario `stick_steps` (new: no roll/pitch/yaw stick segment existed, `rate_step_*` is offboard rate mode), flown with
  `--stick-mode acro` and `--stick-mode stabilized`, 3 seeds each, throttle stick held at hover, sticks over MAVLink
  MANUAL_CONTROL (int +-1000, about 11 bit, ~33 Hz: the G4 stick quantisation). After 3 s settle, per axis roll, pitch,
  yaw in turn: stick +A for 0.5 s, -A for 0.5 s, 0 for 2.5 s. Acro: A = 1 = 100 deg/s (MC_ACRO_*_MAX 100, expo and
  superexpo 0, firmware defaults). Stabilized: A = 0.5 (roll/pitch 0.5 x MPC_MAN_TILT_MAX, yaw 0.5 x MPC_MAN_Y_MAX).
  Acro pass: on the stepped axis, RMS of (commanded rate from the applied sticks - truth body rate) over the plateaus
  [edge + 0.1 s, next edge] of the three edges (+A, -A, 0, the 0 plateau limited to 1.0 s) <= 10 deg/s; the first
  0.1 s after an edge is the rise transient (about 3 inner-loop time constants), reported (rise time, overshoot), not
  gated. Stabilized pass: truth tilt <= 3 deg over [release + 1.0 s, release + 2.5 s] after each roll/pitch doublet
  and after the yaw doublet; truth |yaw rate| <= 10 deg/s over the same window after the yaw doublet. Both: no LOC
  (no ground contact, truth tilt < 80 deg). Checker `bench/g51_check.py` (self-test, second key).
  Test defect fixed S136 (pre-test, no valid result yet): a throttle held at hover sank the craft to the ground in
  both modes (no altitude loop in acro/stabilized). The throttle now comes from the runner pilot (`--stick-pilot`,
  altitude hold on the throttle only; roll/pitch/yaw sticks are the step table alone). Configuration: identified
  gains (`MC_INDI_ID_OK 1`). Recorded: with `MC_INDI_ID_OK 0` (pre-identification, 0.5 x K) the acro roll/pitch
  RMS was 13.6/13.0 deg/s, explained by the halved bandwidth (t90 208 ms = 2.3/(0.5 x 20 rad/s)).
- G5.2 exact test (S138, before its first test; the row did not state stick timing, reference or settle band).
  Scenario `stick_pos_steps` (new segment table: no stick z/xy step existed; `stick_zsine_o6` is a sine), stack and
  config as G5.1 (identified gains), stick model as G5.1, no `--stick-pilot` (the throttle stick is the z demand).
  After 3 s settle: z step = throttle stick at the value giving vz 1.0 m/s up (`MPC_Z_VEL_MAX_UP` 3, expo inverted by
  `stick_profile`) for 2.0 s, then centred for 6.0 s. posctl only, then x step = pitch stick at the value giving
  3.0 m/s forward (`MPC_VEL_MANUAL`) held until 3.0 m of truth travel from the step start or 2.5 s, then centred for
  6.0 s. Flown with `--stick-mode altctl` (z step only) and `--stick-mode posctl` (z and x), 3 seeds each.
  Per step: start = truth position at the stick edge; final = mean truth position over the last 1.0 s of the centred
  window; step size d = |final - start| (reported; d < 1.0 m z or < 2.0 m x is a scenario fault, run invalid).
  Overshoot = max truth excursion beyond final in the step direction after the release edge; pass z <= 0.3 m,
  x <= 0.5 m. Settle = time from release to the last exit of |truth - final| <= 2 % of d; pass <= 4.0 s. Off-axis
  (y, and z during the x step) truth excursion reported, not gated. No LOC as G5.1. Checker `bench/g52_check.py`
  (self-test, second key). Clarification S138 after the first test (no threshold change): |truth - final| is taken
  on the step axis (z, or the horizontal step direction for x), as "off-axis reported, not gated" implies; the x
  step follows the vehicle heading, so x means the horizontal step direction, not NED north.
- G5.3 exact test (S139, before its first test; the row did not state wind profile, reference or window).
  Hold: stick-mode posctl, after 3 s settle the runner switches to HOLD (AUTO_LOITER, MAV_CMD_DO_SET_MODE) with
  sticks centred; 2 s later wind override steady 5 m/s, peak 8 m/s total, along +x (gust_x profile: 2 s ramp, 10 s
  hold, 1 s gust, 15 s tail). Reference = mean truth position over the 1.0 s before the wind starts. Hold RMS = RMS
  of the 3-D truth distance to the reference over [wind start, wind start + 28 s]; pass <= 0.3 m; nav_state 4 over
  the whole window, else invalid. Mission: `auto_tour` (S135 logs reused, no new flight): every mission waypoint
  reached = min truth horizontal distance to it <= 1.0 m (NAV_ACC_RAD acceptance 1.0 m); max truth horizontal
  speed over the mission legs <= 1.1 x the configured cruise speed (MPC_XY_CRUISE, or the item speed if set).
- G5.5 exact test (S139; "G2 trajectory limits" points at no G2 table, the stated trajectory limit is G3 section 3
  item 4). `o1`-`o7` offboard as defined in `bench/scenarios.py`, 3 seeds: truth vs the analytic reference
  (no held reference, lesson 1), horizontal RMS <= 0.5 m and vertical RMS <= 0.3 m over the trajectory segments.
  `offb_vel_step` (vx 2 m/s for 5 s, then 0): RMS(truth vx - 2) over the last 3 s of the step <= 0.2 m/s (10 %),
  |truth vx| at the end of the 4 s hold <= 0.1 m/s, truth max |dz| <= 0.3 m (G3 item 3 height scale). No LOC.
  SET-UP FIX S140 (all G5 rows, no threshold change): nominal plant = GNSS latency 110 ms with matched EKF
  compensation (runner `--gps-dly 110 --gnss-delay 110`). Probes up to S139 flew latency 0 against SENS_GNSS0_DELAY
  110 (estimate leads truth ~110 ms), a G3 mismatch draw, not the nominal plant; they are re-flown at the freeze.
- G5.7 exact test (S139, before its first test; the row did not state stick state, switch order or the attitude
  measure). Scenario `mode_switch10`, stick-mode posctl, runner switches by MAV_CMD_DO_SET_MODE at fixed sim times.
  After 3 s settle, posctl with pitch stick for 3 m/s (as G5.2) for 4 s, then 10 switches, 2.0 s apart, in the
  order P->A, A->P, P->S, S->P, P->H, H->P, P->A, A->S, S->H, H->P (P posctl, A altctl, S stabilized, H hold);
  pitch stick for 3 m/s held in P segments, all sticks centred (throttle at centre) in A, S, H segments; 3 s posctl
  centred at the end. Edges = logged nav_state changes (G1.6 rule); 10 edges with the commanded states, and truth
  horizontal speed >= 1.5 m/s at >= 8 of them, else the run is invalid (speed per edge reported). Per edge:
  thrust step = |mean `vehicle_thrust_setpoint` collective over [edge, edge + 0.1 s] - mean over
  [edge - 0.1 s, edge]| <= 20 % of hover thrust (as G5.4); attitude jump = max truth tilt error (angle between truth
  body z axis and the `vehicle_attitude_setpoint` body z axis) over [edge + 0.3 s, edge + 1.0 s] <= 5 deg. The
  setpoint itself legitimately changes at a mode switch (e.g. hold brakes from 3 m/s); the first 0.3 s (about two
  attitude time constants, 1 / MC_ROLL_P 6.5 = 0.15 s) is the rise, reported (setpoint step, peak error), not
  gated, as in G5.1. No LOC as G5.1. 3 seeds. Checker `bench/g57_check.py` (self-test; second key at the freeze).
  AMENDED S140 (Q7, owner answer A, 2026-11-20, after the first test; defect in the test, not a threshold change):
  HOLD brakes by design, so the speed rule above cannot be met. Validity = truth horizontal speed >= 1.5 m/s at each
  of the 4 edges that leave posctl (P->A, P->S, P->H, P->A); all 10 edges stay gated with unchanged limits
  (`g57_check.py --validity leaveP`).
- G5.11 exact test (S160, before its first scoring; the row did not state reference, window or applied time).
  Flights: the freeze `g5_events` runs (3 seeds), events `ekf_yaw` (+5 deg) and `ekf_xy` (1 m). Applied time t_a =
  first sample where the firmware reset counter increments (`vehicle_attitude.quat_reset_counter`,
  `vehicle_local_position.xy_reset_counter`; Q8 option A). Validity: counter increments once, nav_state constant over
  [t_a - 1 s, t_a + 8 s] (value reported), no other event in that window. Per event, truth only (shared definitions):
  tilt command jump = max over [t_a, t_a + 1 s] of the angle between the `vehicle_attitude_setpoint` body z axis and
  its mean over [t_a - 1 s, t_a) <= 1 deg (body z is yaw-invariant, so the yaw reset is judged on tilt as written);
  truth excursion = max 3-D distance of truth position over [t_a, t_a + 5 s] from its mean over [t_a - 1 s, t_a)
  <= 0.5 m; no sustained oscillation over [t_a, t_a + 8 s] (shared-definition detector, body rates; 8 s gives the
  5 windows of 4 s needed for 3 consecutive flags). Reported: truth yaw change, max setpoint yaw step. z reset 0.5 m:
  not injectable firmware-free (Q8 b); "not tested" until a firmware-free trigger (EKF2_HGT_REF switch probe) or the
  owner answer. 3 seeds. Checker `bench/g511_check.py` (self-test, break-checked; second key before the verdict counts).

### 6. G6 Defaults and identification from a wrong start

Procedure (fixed before the first test): start from physical parameters wrong by x2 and x0.5 each on mass, inertia, motor
tau and thrust constant (8 single-parameter starts plus the 2 all-high / all-low corners = 10 starts, PROPOSED); run the shipped
identification chain once (hover, steps; `rate_fit.py`, D-G1-DERIVE derivation); load the identified parameters; no other edit.
"No manual tuning" is checked mechanically: the parameter diff against the shipped defaults file contains only identified
physical quantities (script lists any other changed name; any one fails). Pass: from each start, G2 (all loops incl. outer),
G3 campaign of >= 100 runs per start-error corner (all-high and all-low; single-parameter starts get the 20-run pre-test set,
PROPOSED: 300 x 10 would be 3000 runs for no added information, the corner starts bound the others) and G5 all rows.
Failure: the identification does not converge in its fixed time budget, or any gate rule fails. Reported only: x500 (~1 kg)
and a > 5 kg vehicle, hover, steps, one trajectory, one gust, margins. Command: `bench/gate_g6.sh start_id`.

### 7. G7 Code (testable parts)

Each as a command with pass rule: (a) `git diff main -- src/modules/mc_rate_control src/modules/mc_att_control
src/modules/mc_pos_control src/modules/control_allocator src/lib/control_allocation src/modules/commander` empty (draft; confirm the
actual module names of the INDI branch, not verified here); (b) unit tests built and passing, each behaviour test fails when the
behaviour is broken (break-check logged); (c) hash of firmware default params == validated parameter files; (d) `make format`
then `make check_format` clean; (e) flash and RAM of one NuttX board measured from the build `size` output, recorded (no estimate);
(f) `.github/instructions` and navigation-terminology rules followed (reviewer checklist, not scripted); (g) the firmware-only branch
from `main` contains no `indi_flight/` path (`git diff --stat main -- indi_flight` empty). Not testable by gate: opus review items
(S58-S63) are a closed-or-justified list.

### 8. G8 Report (testable parts)

Checks: every gate section has an evidence path that exists; G1 evidence limits and G3 excluded corners (beyond-range list) listed;
hardware bring-up checklist present; errata and history appendix present; `git diff main -- docs/ko docs/zh docs/uk` empty;
page lives in `docs/en` only; markdown lint passes if `make` docs target exists (unverified). Command: `bench/gate_g8.sh`.
