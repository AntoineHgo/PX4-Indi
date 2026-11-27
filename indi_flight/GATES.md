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
    ~5 dB conservative (A-50, verdict independent); z no crossing in either.
  - 267 Hz reported (S165, `bash indi_flight/results/g2_freeze_s160/chain267.sh`, seed 1, UNKEYED): rate roll GM 11.5 dB,
    PM 54.3 deg, DM 52 ms (pretest-gate rate RMS 0.0205 vs 0.02 marginal); outer z PT1/PT0 PM 62.8/65.6 deg, no
    phase crossover, DM 245/261 ms (PT0 hole check: 1 hole 6.25 ms, count-disagree flag at 266.7 Hz). Rate GM falls
    19.3/15.4/11.5 dB at 800/400/267 Hz (A-51 trend). Rate x-check S165: xcheck_rate.md, 12/15 agree (A-51).
  - Phase-plateau GM (S164, results/g2_plateau_s164.md, `python3 indi_flight/bench/g2_plateau_gm_s164.py`): 67 cells;
    literal rule 66/67, att ax2_r800_s2 hit by a 0.2 Hz bin with |L| > 1 (gain-reduction margin 18.5 dB). Defect fix
    proposed in Q13 (plateau over |L| < 1, reduction margin >= 6 dB reported); under it 67/67 PASS. Owner Q13 A (S175); rate/att plateau key2 S175.

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
| EKF GNSS delay param | matched (= latency) in 50 %; mismatched (latency + U[-50, +50] ms, min 0) in 50 % (Q24 B, S197; was U[-100, +100]) | | `SENS_GNSS0_DELAY` |
| wind | steady 0-5 m/s plus the existing gust profile, peak 3-9 m/s | uniform | direction uniform; 9 m/s peak = 10 % W (t132) |

Corners (PROPOSED, 10 runs each, every other factor drawn): C1 controller G1 x2 vs plant, tau x3, delay 10 ms (phase worst);
C2 controller G1 x0.5, mass +30 %, thrust 0.7, inertia +30 % (gain worst); C3 saturation corner 2.0 x hover, gust 9 m/s,
mass +30 %; C4 GNSS 250 ms mismatched -50 ms (Q24 B, S197; was -100), wind 5 m/s plus gust, G1 x2; C5 vibration x5, telemetry frozen, dropout 20 %,
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

**Campaign pass**: 0 LOC, 0 sustained oscillation, items 3-6 met in every valid run (no quota: S94 decision 5;
corrected S208, owner Q27 item 5; the earlier ">= 95 %" text here contradicted decision 5). 300 valid runs with 0 safety failures bound the failure rate below 1 % at 95 %
(rule of three, SOURCED standard result). Excluded runs (class (a)) <= 5 % of the total, else the harness is not good enough.
Reported, not pass: per-factor sensitivity of items 3-5; PID on 60 of the same seeds.
Scripts: `bench/g3_sample.py`, `bench/g3_checks.py` (LOC, detector, steady-state) with a second key by a second writer
(G1.3), `bench/metrics.py` for tracking RMS (exists). Command: `bench/g3_score.sh`, `bench/g3_checks.py`, `bench/g3_checks_key2.py` (no `bench/gate_g3.sh` exists).

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

## Owner amendments S175 (2026-11-21): test-defect fixes after first test (owner answers Q8-Q15)
Each fixes a defect of a test; no threshold is lowered. Decision record D-OWNER-Q8-Q15; question text in JOURNAL.md.
- G1.5 / G5 events (Q8 a A): discrete MAVLink events (stream stop, kill, EKF reset command) are referenced to the
  firmware's own applied flag or counter; every G5 transient metric starts there; commanded-applied spread reported.
  The 1-physics-step rule stays for physics injectors (torque, wind, motor, eRPM).
- G5.6 false maybe_landed and G5.11 z reset (Q8 b B): not tested, owner decision Q8(b) (land detector needs ground
  contact; ekf2 external-position reset is horizontal only; no SITL test parameter).
- G5.9a (Q8 add.2 A): "motors 0 within one command period" referenced to the actuator_armed.kill rise; stock
  commander latency switch -> kill reported.
- G5.8 (Q8 add.3): (i) A at 3 m/s, excursion = max horizontal deviation of ground truth from the setpoint/trajectory
  the failsafe action commands, <= 1 m; hover definition unchanged. (ii) A link-loss timeout referenced to the
  firmware's own flag; the ~2.25 s receiver window is reported.
- G5.10 (Q9): (a) tilt limit = MPC_TILTMAX_AIR + 5 deg; alt loss 2.0 m and recovery 5 s unchanged. (b) full-scale part
  flown in stabilized: full throttle + full roll stick for 1 s, same limits. (c) SAT part at a thrust scale where hover
  needs >= 1.0 command for 5 s, after a one-flight check that the motors sit at >= 0.99; the 73 % drop is a G3-type
  side probe, not a G5.10 pass condition.
- G5.2 (Q10 B): z settle band = max(2 % of d, 0.10 m), from the EKF2 height accuracy under the typical profile
  (results/g5_freeze_s157: est - truth -0.078 m at release, decaying over ~5 s).
- G5.5 (Q11 B): limit 0.5 m unchanged; offboard trajectories are flown with the INDI module's own pos/vel feedback
  and flatness feed-forward (design change, not a test change).
- G5.11 (Q12 B + D): xy judged on truth excursion <= 0.5 m and no oscillation; the 1 deg tilt limit kept for yaw,
  with tilt jump = event value minus the 95th percentile of the same metric at no-event instants of the same flight.
- G2 (Q13 A): phase-plateau GM over bins with |L| < 1; bins with |L| > 1 within 10 deg of -180 deg are reported as
  gain-reduction margin 20log10|L| and must also be >= 6 dB.
- G4 Additional (Q14 A): a 20-100 Hz command line is chatter when peak > 20 x median AND its RMS (+-2 Hz) >= one
  DShot step (5e-4 of full scale); ratio reported.
- G4 item 2 (Q15 A): the sustained-oscillation detector skips windows that overlap the 3 s after a nav_state change;
  mode transitions are judged by the G5 transient limits; the land-entry transient is reported for both stacks.

## G4 verdict at freeze-7 (S178, 2026-11-21): NOT PASSED
Evidence: `results/freeze7_s177/G4_SCORES.md` (18 runs, both keyed scripts, S175 rules). R20, C20, R4 and clip rows 18/18
PASS; harsh-hover items 1-3 PASS 3/3 (item 2 both keys). Command chatter (20-100 Hz detector): hover 1/9 FAIL
(hover_harsh_s1, 20.0 Hz, RMS 9.7e-4), cruise 9/9 FAIL on both keys: 33.2-33.5 Hz line through the lemniscate (about
3x floor; the freeze-6 89 Hz line is gone) and the 20-22 Hz line in AUTO_LAND (3.6-9.6x floor). PID on the same cruise
seed was clean (S176), so the failure is INDI-specific. Outside the gate scope, noted: harsh cruise shows sustained
p/q rate flags of 11-13 dps (item 2 applies to harsh hover only). Under the freeze discipline, one session of cause
search (on logs) follows; a fix shown on a log changes firmware, invalidates the G4 rows and re-flies them, and this
verdict is then re-opened.

## G2 verdict at freeze-7 (S179, 2026-11-21): NOT PASSED
Evidence: `results/g2_outer_freeze7_s177/SCORES.md` (24 outer cells, keyed scorer + key2.md),
`results/g2_spot_freeze7_s178/SCORES.md` (2 spot cells, primary only). Outer xy: phase margin 38.4-44.8 deg on 13 of
16 cells (limit 45; worst pt0_ax2_r400_s1 38.4), GM 11.3-12.9 dB, DM 190-280 ms. Outer z: PM 61-71 deg PASS
(pt1_ax3_r800_s1 invalid, no coherent bins). Spot: attitude pitch400_s1 PM 43.0 (freeze-6 53.4) FAIL; rate
roll800_fwdef_s2 PM 47.8 PASS (freeze-6 54.3). Cause: the freeze-7 xy gains MC_INDI_XY_P/VP 1.9/3.6 (D-OFFB-POSVEL,
model predicted 46 deg); its overturn rule is met. Q16 A (PASSED once these cells pass) does not apply. The freeze-6
67/67 evidence stands for the freeze-6 gains only. Next: gain probe (results/g55_gain_probe_s179), then freeze-8.

## Owner amendments S180 (2026-11-21): test-definition fixes Q17 and Q18 (approved by the owner)
Each fixes a defect of a test; no threshold is lowered. Decision record D-OWNER-Q17-Q18; question text in JOURNAL.md.
- G5.10 stabilized full-scale part (Q17 A): no LOC; tilt <= MPC_MAN_TILT_MAX + 5 deg; no windup = attitude error to
  the stick-commanded attitude <= 5 deg within 1 s after the sticks return to centre; the 2.0 m alt-loss limit is not
  applied there (full throttle climbs). PID flies the same flight as the reference.
- G4 command chatter (Q18 A): the 20-100 Hz detector skips 4 s windows that overlap [ground_contact - 1 s,
  landed + 1 s], in both stacks. Touchdown stays judged by G5.4. The skipped land-window values are reported for
  both stacks. The freeze-7 G4 runs are re-scored with the keyed scripts (no re-fly).

## G4 re-score under Q18 (S180, 2026-11-21): verdict unchanged, NOT PASSED
Evidence: `results/freeze7_s177/q18_rescore_s180/KEY1.md`, `KEY2.md` (both keys with the skip, self-tests incl. break
check). Both keys' gate span is the airborne span, which ends 1-2 s before ground_contact: 0 windows skipped, no
verdict moves. Hover 1/9 FAIL: hover_harsh_s1 20.0 Hz, 9.7e-4, all 4 motors, take-off/loiter (not touchdown:
ground_contact 104.5 s, flag at ~12-18 s key 1); PID hover_harsh s1-s3 clean. Cruise 9/9 FAIL: 33.0-33.5 Hz line in
the lemniscate, both keys. The AUTO_LAND 20-22 Hz flags came from the whole-log phase script (S176), not the gate
span; with the span extended to the last sample, land windows hold 20-23.5 Hz 1.2-4.7e-3 (INDI) and 20-26 Hz
1.1-1.5e-3 (PID, 5 runs), reported only. Both keys agree on the GP probe (XY_P 1.2) lemniscate lines m3 33.5 Hz and
m2 89.25 Hz (`results/g55_gain_probe_s179/RECONCILE_S180.md`): F2 targets these.

## G2 verdict at freeze-8 (S182, 2026-11-21): NOT PASSED
Evidence: `results/freeze8_s181/G2_SCORES.md` (24 outer cells, keyed scorer + `g2o/key2.md`; 2 spot cells, primary
only as at freeze-7). Outer: 24/24 PASS on margins (xy PM 49.9-63.7 deg, GM >= 10.8 dB; z PM >= 60.2, no GM crossing;
DM >= 240 ms), holes 24/24 PASS; key2 agrees on 22/24 (pt0_ax3_r400_s2, pt1_ax3_r400_s1 dPM 3.5/3.6 deg > 3 tol, z
PM >= 60 so no verdict effect). Spot: rate roll800_fwdef_s2 PM 41.3 FAIL (freeze-7 47.8, freeze-6 54.3); attitude
ax2_r400_s1 PM 42.2 FAIL (43.0, 53.4), GM 13.6 (19.1). The freeze-7 attribution of the attitude drop to the xy gains
is contradicted (xy back to 1.2, attitude spot unchanged). G2-STEP rows still flying; they cannot lift the verdict.
Next: one session of cause search on the spot drop since freeze-6 (D-FREEZE-8 overturn), PID reference first.

## Owner amendment S183 (2026-11-21): Q19 test-definition fix (approved by the owner)
- G4 command-chatter check (line 362, "the G3 detector, also on the command") applies the Q15 A skip: windows that
  overlap the 3 s after a nav_state change are not counted by the sustained-oscillation detector. Both keys apply it.
- PID guard: chatter lines inside skipped windows are still reported for INDI and PID; the row FAILS if the INDI line
  RMS in a skipped window exceeds the PID reference at the same transition (same scenario and seed).
- Scope: the item 2 rate-detector limit applies to harsh hover; harsh-cruise rate flags are informational (reported).
- Re-score: freeze-8 G4 with keyed scripts (no re-fly); cruise_harsh_s2 flown in the freeze-9 set, G4 scored at freeze-9.

## G2 verdict at freeze-9 (S184, 2026-11-21): PASSED
Evidence: `results/freeze9_s183/G2_SCORES.md` (outer table, G2-STEP, spot, section "Re-score S184" after hole
re-flies; keyed scorer + `g2o/key2.md`). Outer 24/24 meet the limits: xy PM >= 48.5 deg, GM >= 13.4 dB; z PM >= 59.9,
no GM crossing (key2 plateau GM >= 14.0 where found); DM >= 231 ms. Spot (Q16 A): rate roll800_fwdef_s2 PM 47.3, GM
16.1, holes PASS; attitude ax2_r400_s1 PM 47.4, GM 13.2, holes PASS (primary only, as freeze-8). G2-STEP 9/9, both
keys (roll/pitch settle <= 345 of 450 ms, yaw <= 1180 of 1350). Evidence limits carried: (1) pt1_ax3_r800_s1 hole
report FAIL on max gap 13.75/15.0 ms only (missing 0.016/0.017 %, under the 0.1 % of evidence limit 1; the 10 ms bound
was withdrawn by Q2); flown three times, PM 63.1/61.0/59.9, result unchanged, counted. (2) key2 BLOCKED on 3 ax3 cells
(dPM 3.3 deg on two, GM found by key2 only, 20.9 dB, on the third); both keys above the limits in each. (3) rate and
attitude spot margins are thin (+2.3/+2.4 deg). (4) 3 rate x-check groups and A-51 as in Q16 A. 250 Hz not measured.

## G4 verdict at freeze-9 (S184, 2026-11-21): NOT PASSED
Evidence: `results/freeze9_s183/G4_SCORES.md` (18 INDI runs, both keys with the Q19 skip; PID refs `g4_pid/`),
`results/freeze9_s183/g4/Q19_KEY2_REVIEW.md` (second key: skip correct in both keys, guard data correct, guard
comparison not coded, metric undefined in the S183 text -> Q20). Pass: effort R20/C20/R4/clip 18/18; item 1 18/18;
chatter (Q19 skip) 0/18 flagged both keys (max line 4.2e-4, floor 5e-4); item 2 harsh hover 3/3, quiet/typ 12/12,
harsh cruise flagged 3/3 (p 11.9-12.7, q 11.3-12.0 dps; informational per S183); item 3 harsh hover 3/3 (cruise
offsets 0.11-0.22 m reported only, as S180). Fail: PID guard. Flagged-line reading: INDI holds a 20.0-20.8 Hz line
5.0-5.3e-4 inside skipped windows at 5 of 16 transitions (17->4 hover_harsh_s2, cruise_harsh_s1; 14->18
hover_harsh_s1/s2, cruise_harsh_s2), PID unflagged there (2.7-4.4e-4). Any-window reading: 9 of 12 fail. The verdict
is NOT PASSED under both readings. Next: one session of cause search on the INDI 20 Hz transition line (PID clean).

## Owner amendments S187 (2026-11-21): Q20, Q21, Q22 test-definition fixes (owner answers, QUESTIONS.md)
- **G4 PID guard (Q20).** Guard windows only: narrow-band line measure, `psd_windows(..., rms_hz=0.5)` (4 s Hann, 1 s
  hop, peak bin in 20-100 Hz, RMS over peak +-2 bins). Skipped windows as Q15/S183 (`ta < c+3 and ta+4 > c`). A
  transition is checked only where an INDI skipped window is flagged (ratio > 20 AND narrow RMS >= 5e-4); otherwise
  INDI and PID values are reported. When checked: FAIL if PID has no window with ratio > 20 within +-0.5 Hz of the INDI
  peak at that transition (INDI-only line), or if INDI narrow RMS > 1e-3; else PASS (shared transient), with INDI, PID
  and ratio reported. Windows from c+3 s on keep the Q14/Q19 detector (+-2 Hz). Both keys code the rule; freeze-9 G4
  is re-scored without re-fly and that is the G4 verdict.
- **G5.10 SAT part (Q21).** One flight per stack at thrust scale 0.30, 3 m climb plus the 3 m horizontal step. Valid
  only if all 4 motors stay >= 0.99 for >= 1 s in BOTH stacks. If valid: limits unchanged (no LOC, alt loss <= 2.0 m,
  tilt <= MPC_TILTMAX_AIR + 5 deg, back within 0.3 m in <= 5 s after saturation ends), saturation time and hover
  estimate reported. If not valid: SAT part dropped, G5.10 = stabilized full-scale part (Q17 A); saturation under the
  position loop stays covered by G3 C3 (C3 is above the hover-estimate clamp; reported with C3).
- **G3 box (Q22).** G1 error, controller vs plant, per axis: x[0.8, 1.2] (was x[0.5, 2]); log-uniform. Motor tau: tau_up
  and tau_down both lie in x[0.5, 3]: slow = scale, fast = max(scale / asym, 0.5) (test defect: tau_down reached x9).
  Corners C1/C2/C4 use e 1.2 / 0.8 / 1.2 in place of 2 / 0.5 / 2. Payload added after identification (e ~1.3) is a G8
  limit. Run 17 of the S173 pre-test (e 1.52) is out of box: reported with both stacks' values, not in the pre-test set.
  Before the re-fly, the rate-loop model is checked at e 0.8, tau x0.5, 10 ms (fast-motor corner).

## G4 verdict at freeze-9 under Q20 (S187, 2026-11-21): PASSED
Evidence: `results/freeze9_s183/G4_SCORES.md` (all rows other than the guard, S184, both keys), guard re-score under
the S187 rule (no re-fly) in `results/freeze9_s183/g4/GUARD_Q20_KEY1.md` and `GUARD_Q20_KEY2.md` (scripts
`bench/g4_guard_q20_key1.py`, `bench/g4_guard_q20_key2.py`, written independently, each with a synthetic self-test).
Both keys: 54 transitions in 18 INDI runs, 0 checked, 0 FAIL; max INDI narrow-band RMS in a skipped window 4.84e-4
(hover_harsh_s2 17->4, 20.0 Hz), below the 5e-4 flag; 14->18 2.3-2.95e-4. Reported, not checked: 17->4 INDI/PID narrow
RMS 2.94/3.78, 4.84/4.28, 4.47/3.93, 2.86/3.88 e-4 (4 s windows, ratio 0.78-1.14). With effort 18/18, item 1 18/18,
chatter 0/18, item 2 and item 3 harsh hover 3/3 (S184), every G4 row passes. Limits carried: harsh-cruise rate flags
informational (S183); cruise item-3 offsets 0.11-0.22 m equal PID (S180); the 20 Hz take-off->loiter transient exists
in both stacks at 0.05 % of full command; cruise_harsh_s2 exclusion of freeze-8 is history only (freeze-9 flew it).

## G4 verdict at freeze-10 (S194, 2026-11-22): PASSED
Evidence: `results/freeze10_s193/G4_SCORES.md` (18 INDI runs re-flown at FREEZE-10 firmware 7fe6206fcc, scored by
the keyed freeze-9 scripts, both keys, Q19 skip; Q20 guard both keys; PID refs `g4_pid` = freeze9_s183/g4_pid, PID
path unchanged by the freeze-10 commits, which touch only the INDI modules). Effort R20/C20/R4/clip 18/18; item 1,
chatter, item 2: 18/18 both keys, no key disagreement; Q20 guard 54 transitions per key, 0 checked, 0 FAIL, max INDI
narrow RMS 3.46e-4 < 5e-4; guard self-tests 8/8 and 9/9. Nearest limit: K1 chatter line 4.12e-4 (cruise_harsh_s2).
Limits carried as at freeze-9: harsh-cruise rate flags informational (S183); cruise item-3 |dz| 0.135-0.333 m (fz9
0.10-0.22) is read in a window after AUTO_LAND (RECONCILE_S180 task 2, both stacks), not a G4 row.

## G2 verdict at freeze-10 (S194, 2026-11-22): PASSED
Evidence: `results/freeze10_s193/G2_SCORES.md` (outer table, spot cells, G2-STEP, section "Re-score S194" after the
hole re-fly; keyed scorers as freeze-9, `g2o/key2.md`). Firmware 7fe6206fcc (FREEZE-10). Outer 24/24 meet the limits:
PM >= 49.1 deg (pt0_ax2_r400_s2), xy GM >= 13.5 dB, plateau GM >= 12.9 dB, DM >= 229 ms (pt1_ax3_r800_s1); holes
24/24 PASS after re-flying pt1_ax2_r400_s2 once (single 22.5 ms setpoint gap; re-fly PM 56.9, GM 13.9, holes PASS;
original kept in g2o/orig_s194/). Spot (Q16 A): rate roll800_fwdef_s2 PM 46.9, GM 15.7, DM 75.5 ms, holes PASS;
attitude ax2_r400_s1 PM 48.0, GM 13.7 dB, DM 93.5 ms, holes PASS; its -180 crossing at 0.237 Hz with |L| 7.3 is a
gain-reduction margin of 17.3 dB >= 6 dB under Q13 A. G2-STEP 9/9 both keys (roll/pitch settle <= 347.5 of 450 ms,
yaw <= 1196 of 1350). Evidence limits carried as freeze-9: (1) key2 BLOCKED on 3 cells on key agreement only, both
keys above the limits in each (pt1_ax1_r800_s1 PM 71.3/67.8; pt1_ax3_r400_s2 PM 58.7/58.2, GM key2 only 16.3;
pt1_ax3_r800_s2 GM 22.4/17.8); (2) rate and attitude spot margins thin (+1.9/+3.0 deg); (3) 3 rate x-check groups and
A-51 as Q16 A. 250 Hz not measured.

## Owner amendments S197 (2026-11-22): Q24 B and Q25 B test-definition fixes (owner answers, QUESTIONS.md)
- **G3 GNSS delay mismatch (Q24 B).** The EKF GNSS delay draw is latency + U[-50, +50] ms (min 0) in the mismatched
  50 % (was U[-100, +100]); corner C4 uses -50 ms. Reason: +-100 ms exceeds what a correct bring-up leaves; the S192
  matched-GNSS probe shows draws 02/05 pass. New F-3 requirement and bring-up item: EKF2/SENS GNSS delay set within
  50 ms of the measured GNSS latency (design/airframe_requirements.md). Draws 08 and 03 (key 1), which fail with PID
  on the same draws, are reported in the G3 evidence as scenario properties shared with PID, not counted against
  INDI. The freeze-10 pre-test result under the old range (16/20 both keys) stays in the evidence. Re-run plan:
  D-OWNER-Q24. No firmware or config change; FREEZE-10, G2 and G4 verdicts stand.
- **G5.5 horizontal trajectory limit (Q25 B).** The absolute 0.5 m horizontal RMS limit is a steady-state hover
  limit and a test defect on moving trajectories. For each `o1`-`o7` row the horizontal limit is
  H_lim = max(0.5 m, tau_att x v_rms), v_rms = RMS of the analytic reference horizontal speed over the same
  trajectory segments as the error RMS, tau_att = 1 / MC_ROLL_P of the reference airframe = 1 / 8.0 = 0.125 s
  (`4040_gz_quad5in`, MC_ROLL_P = MC_PITCH_P = 8.0, set at stage 1). Derivation and sources: D-OWNER-Q25; written
  before any re-score, from scenario and airframe constants only. Expected values: o2 about 0.62 m (5 m/s),
  lemniscate rows about 0.53 m (4.24 m/s RMS), z-sine rows 0.5 m (floor); the scorer tables the exact values. The same
  limit applies to the PID reference; both stacks are reported against it. Vertical 0.3 m and the `offb_vel_step`
  rows are unchanged. Re-score only, no re-fly.

## G5 verdict at freeze-10 (S198, 2026-11-22): PASSED
Evidence: `results/freeze10_s193/G5_SCORES.md`, `G5_5_RESCORE_Q25.md` (+ `G5_5_LIMIT_KEY2.md`), `G5_VERDICT_AUDIT.md`
(row table), `g5_gaps_s198/README.md` (events seeds 2-3), `g5_gaps_s198/moving/G58_KEY1.md` and `G58_KEY2.md`
(G5.8 at 3 m/s). All flights on the FREEZE-10 binary (7fe6206fcc, built 2026-11-21 22:38), INDI stack, 3 seeds per row.
- G5.1 acro/stab, G5.2 altctl/posctl, G5.3 hold, G5.4 take-off/land, G5.5 o1-o7 (Q25 B limit) and offb_vel_step,
  G5.7, G5.10 stabilized full-scale: PASS 3/3 per row, both keys (G5_VERDICT_AUDIT.md table).
- G5.8 hover rc/link/offboard loss: PASS 9/9 (entry <= 0.51 s after timeout, excursion <= 0.121 m). G5.8 at 3 m/s
  (Q8 add.3 (i), scorer two independent keys written S198): PASS 9/9, hold entered on every event, excursion
  0.16-0.25 m (limit 1 m), keys within 0.012 m; PID reference seed 1 0.46-0.51 m.
- G5.9a-d kill / re-arm: PASS 3/3 each (kill outputs 0 within 1.25 ms of the kill rise; re-arm states zero; first
  second <= 0.01 %; take-off after re-arm step 4.0-4.7 % of hover, dip 0 m).
- G5.11 ekf_yaw (excess <= 0.12 deg over no-event p95) and ekf_xy (truth excursion <= 0.248 m, Q12 B): PASS 3/3.
- F-7: no thrust step at the ramp -> flight edge beyond the G5.4 limit (edge step <= 10 % of hover in every take-off).
Read on the gate definitions, not on legacy script prints: key-2 G5.9a uses the switch reference (+6.25/+10 ms, value
after the kill rise is 0-1.25 ms); key-2 G5.11 raw 1 deg rule (s3 1.003 deg raw, excess 0.06 deg) and obsolete xy tilt
rule; key-2 G5.9b/9c print no verdict, values inside the limits. Limits of the evidence: G5.3 mission and G5.4 RTL have
key 1 only (no key-2 script exists; as at freeze-9); mission waypoint margin 0.03 m (worst 0.970 m vs 1.0 m).
Not tested: G5.6 and G5.11 z reset (owner Q8(b), S175); accel-only offboard and take-off on an offboard setpoint alone
(owner decision F-8); G5.10 SAT part dropped (Q21: no stack reaches 4 motors >= 0.99 for 1 s).

## G3 verdict at freeze-10 (S199, 2026-11-22): NOT PASSED
Evidence: `results/g3_campaign_f10/` (300/300 runs at speed 4, FREEZE-10 binary d220e193, `SCORES.tsv`, both keys per
run), `FAILS_S199.md` (classification), `results/g3_refly_s199/SUMMARY.md` (speed-1 re-fly and PID reference of the same
draws, campaign speed rule and reference-before-cause rule).
- Item 1 (no LOC, no quota): FAIL. Run 245 (corner C1: controller G1 x2, tau x3, delay 10 ms) diverges in a growing 2 Hz
  pitch oscillation and falls (watchdog height < 0.3 m at 64.7 s; speed 1: 65.05 s). Run 264 (corner C3: saturation hook
  0.351 with weak motor 0.709) tilts past 60 deg at the fault (60.7 s; speed 1: 60.9 s). PID flies both draws without LOC.
- Item 2 (no sustained oscillation, no quota): FAIL. 79 of 297 scored runs fail on at least one key (key 1 73, key 2 45).
  Real lines: class A, 10.75-11.5 Hz pitch, 8 runs (high delay, fast motor, controller G1 below plant); class B, 2.0-2.5
  Hz, 37 runs (high delay, slow motor; corners C1 and C6 fail 19/19 scored). Reproduced at speed 1 on 283 (A) and 239
  (B), where PID passes; 008 (A) also fails for PID (other axis, 161-207 dps), a draw shared with PID. Class C (25 runs,
  key 1 only) are landing windows that key 2 skips by design; class D (9, key 1 only) are borderline 2 Hz lines.
- Items 3-6: 15 item-3 misses in 297 scored runs (94.95 %, all within the speed-1 spread of their limit); items 4-6
  not reported separately by the classification. Not decisive given items 1-2.
- Aborts: 039 is a harness artefact (LAND overridden by the stick re-centre; both stacks hover until the wall
  timeout, re-flown at speed 1), not a control failure.
The remaining 77 item-2 indices were not re-flown at speed 1: the verdict does not depend on them (item 1 fails on two
confirmed, INDI-specific runs). Step back: QUESTIONS.md Q26.

## Owner amendments S208 (2026-11-22): Q27 test-definition changes after the first G3 test (owner answer, QUESTIONS.md)
- **G3 controller ACT_TC (Q27 item 1).** The plant motor tau stays drawn x[0.5, 3] with up/down asymmetry (owner range).
  The controller `MC_INDI_ACT_TC` is drawn as identification error, like the controller G1 error: its box is written
  here from the measured error bound of the ACT_TC identification step (G6, D-OWNER-Q27), before any G3 flight. Until
  then no G3 flight. The freeze-10 campaign (controller ACT_TC 0.033 fixed, ID_OK 1) stays as evidence, NOT PASSED.
- **Items 3-6 (Q27 item 5).** No quota (S94 decision 5); the "Campaign pass" text above is corrected. Every item 3-6
  miss in a valid run is a failure after the speed-1 re-fly rule. The 15 freeze-10 misses are re-flown at speed 1
  when the next G3 campaign is scored.
- **Class C (Q27 item 6).** Q15 A (skip item-2 windows overlapping the 3 s after a `nav_state` change) applies to G3
  item 2 on both keys (key 1 `g3_score.sh --skip-nav-change`). Change after the first test: key 2 had applied it
  without this text. The G3 evidence tables the skipped land-entry lines for both stacks and the PID result on the
  class C draws. G5 flies the nominal plant only and is not claimed to cover these windows.
- **Harness aborts (Q27 item 8).** A harness abort (wall or land timeout, runner exception, LAND overridden by the
  stick re-centre as in 039) is an invalid run, scored INVALID by both keys and re-flown; never PASS. Class (a) limit
  (<= 5 % excluded) unchanged.
- **G6 un-identified state (Q27 item 7).** New G6 item: about 100 Latin-hypercube runs over the full G3 box (plant tau
  x0.5..3) plus the box corners, flown at `MC_INDI_ID_OK` 0 (gains x0.5, ACT_TC 0.05). Pass: item 1 (no LOC) in every
  valid run, item 2 (no sustained oscillation) inside the identification-manoeuvre window. Item 2 elsewhere and items
  3-6 reported. The freeze-10 x0.5..3 result (ID_OK 1, ACT_TC 0.033) is never labelled "the unidentified limit".
- **Model margin limit (Q27 item 3).** K fixed 20, no 1/tau_c scaling. The report (G8) states the model margins over
  the realised G3 box (best rule about 36 deg PM / 5-7 dB GM, below G2's 45 deg / 6 dB, which is measured on the
  nominal plant) as a limit, with the 3 dB model optimism seen on 283.
- **264 (Q27 item 4).** Reported as a limit (CW rotor-speed collapse hits both stacks; INDI applies 55-80 % of PID's
  counter-torque for 0.2 s and tilts over, PID recovers; origin of the collapse untraced). No K change for it.

### 6c. ACT_TC identification error (S208, written before the estimator is built; Q27 item 1, D-ACTC-IDENT)
Procedure: `design/actc_ident_s208.md`. Estimator `bench/ident_actc.py`, output-error fit per motor of
(rpm/rpm_max)^2 against the motor command with tau_up, tau_down, delay, gain, intercept, plus a symmetric tau_sym.
- Estimator acceptance (before any SITL use): synthetic self-test passes (noise-free: each tau within 2 %, delay within
  one sample; with eRPM quantisation, noise, telemetry 0-3 frames, delay 0-10 ms and a closed-loop case: within
  10 %; a forced 10 ms delay mismatch and an unexcited command each fail the fit-quality check), and a second key.
- SITL measurement: the 30-flight grid of the design note (plant tau_slow x{0.5, 1, 2, 3}, asymmetry {1, 3 down-slow,
  3 up-slow}, (delay, telemetry frames) {(0, 0), (10 ms, 3)}, seed repeats and marginals), ID_OK 0 configuration,
  after a 2-flight pre-test. Valid identification: fit-quality check passed and seed-to-seed spread of tau_sym
  <= 10 % on the repeated cells (D-IDENT condition (i) tolerance). A cell that fails is a failed identification,
  counted and reported, never dropped.
- Result: the table of estimate / truth and min / max / 95 % of tau_sym_hat / tau_slow and tau_sym_hat / tau_mean
  over valid cells. This is the measured bound. The G3 controller-ACT_TC box and the ACT_TC rule are proposed from
  it to the owner (Q28) and written in this file before any G3 flight. No threshold on the bound is set here.

## Owner amendment S211 (2026-11-23): Q28 G3 controller-ACT_TC box and ACT_TC rule (owner answer A, D-OWNER-Q28)
- **ACT_TC rule.** `MC_INDI_ACT_TC` = median over the 4 motors of the identified tau_sym (`bench/ident_actc.py`,
  telemetry esc_status instance 0), no rounding, no cap. The identified delay (actuator plus telemetry) is not fed
  to any delay parameter.
- **G3 controller-ACT_TC box.** Per run, controller `MC_INDI_ACT_TC` = r x plant tau_mean x 0.033 s, tau_mean =
  (tau_up + tau_down) / 2 of the drawn plant, r uniform [0.88, 1.02], drawn independently of the other factors.
  Basis: 6c bound on instance 0 (median-of-4 r_mean 0.898-1.004) +-2 % estimator allowance (upper edge = max + 1.6 %);
  results/actc_grid_s209 (REFIT_INST0.md, BOX_MARGINS.md, Q28_REVIEW.md). Replaces the freeze-10 fixed 0.033.
- **Limits reported with the G3 result.** Bound valid for the median of 4 only (single motors 0.843-1.040 on the roll
  injector); 2 % allowance equals the largest seed spread seen (4 pairs); one seed, roll injector, sim speed 4; the
  linear model is flat in r above 1.02, the upper edge rests on flight evidence (283 fails at x1.5).
- **Order.** G3 re-fly (300 runs, S208 amendments apply) and G6 item 7 in one chain, after the sampler draws r and the
  runner sets the controller ACT_TC from it (reviewed before any flight).

## Owner amendment S211b (2026-11-23): Q29 G3 re-fly order and G6 item 7 size (owner answer A, D-OWNER-Q29)
- **G3 re-fly: 300 valid runs kept (floor and < 1 % claim unchanged), flown critical first.** Block 1: the 60 corners
  C1-C6 and the 50 freeze-10 LHS draws that failed or aborted (same sampler seeds, plus the S211 r draw). Block 2: the
  other 190 LHS draws. The chain halts on the first item 1 or item 2 failure confirmed on both keys (after the
  speed-1 rule for item 2); a halted campaign is NOT PASSED and goes to the owner. Order changes no pass criterion.
- **Freeze-10 item-3 misses.** The speed-1 re-fly of the 15 freeze-10 misses (S208 amendment) is dropped: they were
  flown at ACT_TC 0.033; misses of the new campaign go through the speed-1 rule.
- **G6 item 7 (S208 amendment) reduced to the 60 corners** C1-C6 at `MC_INDI_ID_OK` 0, pass as written there. The
  ~100 LHS runs are dropped; G8 reports the reduced coverage as a limit.

## G3 verdict, re-fly with drawn controller ACT_TC (S213, 2026-11-23): NOT PASSED (campaign halted)
Evidence: `results/g3_refly_actc_s212/` (chain C212, freeze-10 firmware and params, controller ACT_TC drawn in the S211
box; SCORES.tsv, progress.txt, HALT_ON_FAIL.json) and `speed1_s213/README.md` (speed-1 and PID reference flights).
- 25 runs flown (block 1, critical first). Halt 1, run 022 (draw 262, C3): item 2 FAIL on both keys at speed 4, not
  reproduced at speed 1 (S208 rule), so not counted; the chain resumed. PID on the same draw fails item 2 (2.0 Hz).
- Halt 2, run 024 (draw 264, C3: thrust scale 0.351, motor 3 at 0.709, mass 1.3): item 1 loss of control, tilt > 60 deg
  at 60.78 s (speed 4) and 61.03 s (speed 1), controller ACT_TC 0.0177. The freeze-10 flights of the same plant
  (ACT_TC 0.033) lost control at 60.67 s and 60.91 s: the failure does not depend on ACT_TC. PID flies the draw without
  loss of control (tilt max 40 deg). Under S211b a halted campaign is NOT PASSED; under the failure-explanation rule
  this is an INDI-specific failure, class (b) or (c) still to be shown by factor restoration (Q31).
- Item 3 is not scored for the verdict: its window is open in Q30 (run 022 0.308 m at speed 1 against 0.30 m).

## Owner amendment S214 (2026-11-23): Q30 G3 steady-state window (owner answer B, D-OWNER-Q30)
- **Window.** Every G3 scenario ends with a hold of >= 20 s that starts at the arrival from the main segment. All
  injected events (fault steps, eRPM loss/frozen, gust) end before that hold; the steady wind stays on and the sag stays
  at its final value to the end of the run (no wrench clear, no ramp inside the hold). Item 3 window = last 10 s of that
  hold, so it starts >= 10 s after the last transient (item 5: 5 s recovery + 5 s no re-excursion). Item 6 uses the last
  20 s of the same hold. Thresholds unchanged. Replaces the 3 s stand-in window of `bench/g3_score.sh`.
- **Implementation.** Dedicated G3 scenarios in `scenarios.py` (position and stick), not edits to `o1_lemniscate` /
  `stick_zsine_o6` (used by G5). Steady wind held to the scenario end; sag ramp fixed at the drawn length. Key 1 and key 2
  each derive the window from `run.json` (key 2 no longer takes key 1's t0/t1). Items 5 and 6 implemented in both keys.
- **Correction (GATES 3 "Flight per run").** Gust and faults are injected at the start of the main segment (`traj` /
  `stick`), not at the start of the hold, as the runner has always done.
- C212 (3 s window) stays as items 1-2 evidence; its item-3 scores are not used. Restart is decided by Q31.

## Owner amendment S218 (2026-11-23): Q31 route and gate binary (owner answer B, D-OWNER-Q31, D-BINARY-GZFIX)
- **Gate binary.** SITL binary sha256 903eae63ceb1bf019215076650cf02fb38cac8534618530410506f6a505f6d62 (FREEZE-10
  sources + GZBridge parameter fix f110361a33; results/q31_injector_fix_s214/README.md) replaces d220e193 for every gate
  flight from S218. Controller code identical (only GZBridge symbols differ; other frozen build files unchanged).
- **Validity of earlier runs.** Every pre-S214 run with a multi-motor SIM_GZ_EC_* write (saturation draws: C3 corners,
  freeze-10 and C212) fails GATES 2 run validity (motors limited ~1 s apart); weak-motor-only runs had the step up to
  1 s late; the sag staircase moved in 1 s steps. Earlier verdicts stand only on their other runs; C3 results are
  re-flown on the new binary, never used as failures or passes.
- **Route on draw 264 (C212 idx 24).** (1) Factor restoration at speed 1 (GATES 2 "Failure explanation"), then one
  fix probe if a cause is shown on the log; class (b) goes to the owner. (2) If the LOC persists: two independent
  investigation agents in parallel (opus, effort high), separate reports; then one solving agent (opus, high) and an
  independent review agent (pre-approved). (3) If it still persists: owner question, continue or stop.

## Owner amendment S225 (2026-11-25): Q32 bounded re-freeze route and G3 item 2 fault windows (owner answer A, D-OWNER-Q32)
- **Route.** FREEZE-10 decision 2 (D-RATE-BLD-2) re-opened, rate loop only. Candidates (i) lower ACT_BLD, (ii) per-motor
  command-to-omega^2 correction, (iii) bounded rate integrator with allocator-saturation anti-windup; one pass line,
  simplest passing candidate wins. Bound: one solver run (opus, high), one independent review (opus, high); any missed
  cell = fail; no candidate passes -> route B below, no new question.
- **Order.** Q30 tooling first (S214 window, items 4-6 in both keys, item 2 rule below), then FREEZE-10 baselines of
  draws 262 (C212 idx 22) and 283 (C5) on 903eae63.
- **Pass line** (written in D-RATE-BLD-2 before the first candidate flight, unchanged after): draws joint, 264, 262, 283,
  speed 1, committed seeds, one flight each; both keys: item 1 pass, item 2 pass (rule below), item 3 pass on the S214
  window. A cell FREEZE-10 already fails on 262/283 is judged "not worse" and reported as a G3 risk. Items 4-5
  reported. Winner re-flown once on 264 and joint: still passes. G2 rate roll/pitch/yaw at 800 and 400 Hz, measured
  and model-only, 2 seeds, at G2 thresholds; G2-STEP 9/9. Unit tests break-checked: weak-motor loop, allocator-
  saturation anti-windup, landed, telemetry loss and frozen, arming reset. New code meets F-10.
- **A passes.** Freeze-11 = FREEZE-10 + the candidate only, built per D-BINARY-GZFIX, sha pinned. Re-fly G2 rate/att
  cells + G2-STEP (outer cells only if the outer loop changed), G3 300 fail-fast, G4, G5 rows, G6 item 7. A failure
  there goes to the owner.
- **Route B.** Keep FREEZE-10. Excluded corner, fixed now: saturation-corner draws (2.0 x hover, outside owner ranges,
  S94 decision 6) with a weak motor on; class (b), a measured INDI limit reported in G8 (not a PID fallback, F-1).
  In-range draws (sag, weak motor >= 0.7) stay counted. G3 re-flies 300 fail-fast on 903eae63.
- **G3 item 2 fault windows (applies from S225).** Item 2 skips every 4 s window that contains a fault or gust step
  start (main-segment start, read by each key from `run.json`); no line chains across a skipped window. Telemetry
  loss/frozen starts are not skipped. Conditions: item 5 scored in both keys in the same campaign; self-test in both
  keys (straddling sine not flagged, post-fault sine flagged, break-checked); skipped windows tabled for both stacks.
  Rescore only valid 903eae63 runs used on this route (4 draws, PID references); pre-S214 multi-motor runs stay invalid.

## Owner amendment Q33 (2026-11-25): G3 item 5 events on a static reference (owner answer B with amendments, D-OWNER-Q33)
- **Supersedes** the S214 "Correction (GATES 3 Flight per run)": fault steps, wind ramp and gust now start in an
  event hover between settle and the main segment, not at the main-segment start. S214 window and hold rules unchanged.
- **Scenario.** settle -> event hover -> main segment (`traj` lemniscate / `stick`) -> hold (35 s). In the event hover:
  fault step and wind ramp at t0, gust at t0 + 12 s (fixed gust_x timing). Event hover length >= gust end + 10 s,
  derived in code from the `bench/disturbance.py` profile constants (23 s today). Steady wind and drawn faults stay on
  to the end of the run. Sag: slow ramp from the scenario start as now, not an event; its ramp end is tabled per run.
- **Item 5.** Events = fault start (t0) and gust (t0 + 12 s), in both keys. Reference per mode: position = hover
  setpoint (trajectory_setpoint); attitude = q_d (level, zero sticks); rate mode = not applicable. Wind ramp not
  scored. Thresholds unchanged. Replaces the D-G3-KEYS-S227 item 5 reference (commanded path at the same time).
- **Item 2.** S225 skip windows also contain the gust time (t0 + 12 s) in both keys; self-tests break-checked.
- **Item 4.** Window = main segment only; limits unchanged.
- **Evidence.** S227 pre-test (INDI and PID) stays evidence for items 1-3, 6 only. Before any campaign: re-fly pre-test
  draw 0 for INDI and PID on the new scenario, both keys; then the FREEZE-10 baselines 262/283 on the new scenario.
  PID failing item 5 on the new scenario -> owner question.

## G3 verdict, route B (S242, 2026-11-26): NOT PASSED (campaign halted at run 003)
- Route B (Owner amendment S225), 300 fail-fast on 903eae63, results/g3_routeB_s239/campaign: halted at run 003
  (HALT_S240.md). Speed-1 re-fly and PID references: results/g3_routeB_s239/REF_S241.md (keys 1 and 2 agree on
  every item).
- Item 2, draw 3 (slow motors tau x2.4-2.8): INDI q line at 2.00 Hz, sustained, both keys, reproduced at speed 1.
  PID on the same draw and seed: item 2 PASS. INDI-specific failure -> G3 NOT PASSED.
- Item 4, draws 2 and 3: INDI 0.834 / 0.553 m (re-fly 0.546 m), PID 0.862 / 0.917 m, limit 0.5 m. Fails in both
  stacks: whether this is a test defect is owner question Q35 (blocking for item 4 rows). It does not change the
  verdict, which item 2 decides.
- Route B was the last route of D-OWNER-Q32: next step is owner question Q35.

## Owner amendment S243 (2026-11-26): Q34 item 5 reading and Q35 final G3 verdict (D-OWNER-Q34-Q35)
- **G3 final: NOT PASSED for this project** (Q35 A). The G3 chain stops: no re-fly, no new firmware route. The
  slow-motor 2 Hz pitch mode (draw 3, S241 re-fly, local q PSD peak 2.0-2.25 Hz about 30 dB above PID on the same
  draw) and the draw 264 LOC are written up in G8 as measured INDI limits, with the data. Hypothesis to state as
  UNVERIFIED unless checked: actuator-model mismatch (motor tau x2.4-2.8 nominal, MC_INDI_ACT_TC 0.033).
- **Item 4, PID guard** (Q35 C yes): a row where PID fails item 4 on the same draw and seed is a test defect,
  reported for both stacks and not counted against INDI, ONLY IF INDI's value is not worse than PID's; otherwise it
  counts against INDI. Today: draws 0 (0.418 vs 0.768 m), 2 (0.834 vs 0.862 m), 3 (0.553 vs 0.917 m): not counted.
  Limit: one flight per stack and draw, no spread estimate.
- **Item 2 note:** the 20x band-median ratio passes in every window for both stacks (ratios 1e4-1e7); the 5 deg/s
  RMS floor decides item 2 in practice.
- **Item 5 = "A and B"** (Q34): an event passes only if (A) t_rec <= 5 s and no position re-excursion > 0.3 m in
  (t_rec, t_rec + 5 s], and (B) position error <= 0.3 m and tilt error vs q_d <= 3 deg on every sample in
  [event + 5 s, event + 10 s]. Both keys change; re-score of the 4 S230 pre-test runs must reproduce the owner's
  values (INDI d0 fault/gust PASS, PID d0 fault/gust PASS, INDI d262 fault FAIL on A, d262 gust PASS). Serves the
  G3 rows and the G8 write-up only, not a new campaign.
- **G6 consequence (orchestrator reading):** G6 requires G3 passed from wrong initial parameters; with G3 final NOT
  PASSED, G6 cannot be PASSED in full. G6 items that do not depend on G3 (identification procedure, item 7, G2/G5
  rows) are still flown and scored; the G6 verdict will state the G3 dependency.

## G6 item 7 verdict (S244, 2026-11-26): NOT PASSED; G6 NOT PASSED

Runs 240-299 (60 corners, `MC_INDI_ID_OK` 0, gate binary 903eae63), scored by both keys
(`results/g6_item7_s212/SCORES.tsv`, `TALLY_S244.md`). Pass rule (S208 item 7): item 1 (no LOC) in every valid run.
- Item 1 FAILS: LOC in 278 and 295, both keys. Runs 262 (altitude loss), 264 (height < 0.3 m), 269 and 292
  (tilt > 60 deg) were stopped by the flight watchdog. The chain marked them INVALID, but the Q27 item 8 list of harness
  aborts does not include a watchdog stop, so they count as LOC here too: 6 LOC in 58 runs.
- Invalid (harness): 274 (wall timeout), 284 (no INDI status in log). They are not re-flown because they cannot
  change the verdict.
- Reported: item 2 over the whole run 21 (key 1) / 22 (key 2) runs (key disagreement on 276 only; the window-limited
  item 2 was not scored separately); item 3: 2, item 4: 18, item 5: 30, item 6: 0 runs fail. Run 240 item 5 was
  scored before the Q34 key change (rescore found nothing to redo, so it is not re-checked).
- G6 needs G2, G3 and G5 to pass. G3 is final NOT PASSED (S243), so G6 is NOT PASSED. The identification procedure
  and the defaults evidence stay in G8 as the method and its limits.

## G7 verdict (S252, 2026-11-27): PASSED, with the justified limits below
Head feat/indi-flight 689348de10 (firmware dirs identical to local branch indi-fw-pr ee7d4542d7, not pushed, no PR).
- (a) Stock modules zero diff: PASS, 0 lines over the 6 stock paths, 0 indi_flight/indi_project paths, 75 files
  (results/g7_s251/README_P2.md).
- (b) Tests: PASS. 12/12 gtest targets, 239 tests, on the branch. The S195 audit (66 mutations, all 9 survivors
  killed, results/g7_s195/BREAK_AUDIT.md) covers the helpers incl. injection (S196). The 4 MISSING and 3 WEAK rows of
  results/g7_s249/G7B_TEST_INVENTORY.md are closed by tests that fail when broken (results/g7_s250/P6A_TESTS.md,
  g7_s251/P6B_TESTS.md); the 11.3d hand-computed torque test is in g7_s251/P7B_TORQUE_TEST.md. Justified, not
  unit-tested: module glue (parameter -> setter wiring for XY_P/XY_VP, ERPM_TO, SP_TO, INC_MAX; sp_source call site;
  pos omega_ff valid flag; esc_status instance 0) is covered by SITL gate rows (G2 outer cells, g55_gain_probe_s176,
  G5) per D-G7-HARNESS; the K_pos/K_vel path is unreachable (module always accel_only); the jerk source (D-JFF-SOURCE)
  is flown in g4_jff_s172; the lower clamp in normalisedThrustFromRpm is dead code (rpm^2 >= 0); a permanently
  saturated motor with frozen eRPM is not detected by design, pinned by a test, written in report 04_limits.
- (c) Defaults: met as defined in D-G7-DEFAULTS. Gains: 0 mismatches between firmware defaults and the validated
  files (results/g7_s195/DEFAULTS_DIFF.md, a full diff in place of the hash). Physical parameters (W_MAX, ACT_TC) are
  per airframe; MC_INDI_ID_OK 0 (un-identified start) is a reported limit (D-ID-OK-LIMIT, G6 item 7 6/58 failures).
  Not a robustness claim: G3 is NOT PASSED for every configuration.
- (d) Format: PASS, astyle 50/0 on the branch (g7_s251/README_P2.md); later commits are docs only.
- (e) Size: PASS, measured at this head (results/g7_s252/NUTTX_BUILD.md): px4_fmu-v5x with both modules, rc 0,
  0 warnings, +64 792 B flash (8 964 B left), +40 B data, matching S195 within 120 B. Limit: fmu-v6x overflows by
  23.5 kB with both modules (S195, results/g7_s195/FORMAT_SIZE.md).
- (f) Instructions and F-10: PASS. Whole-branch review results/g7_s248/F10_WHOLE_BRANCH_REVIEW.md, fixes second-keyed
  (g7_s249/P3B_KEY2.md), delta review of 0b1c6a26d1..HEAD results/g7_s252/F10_DELTA_REVIEW.md (0 BLOCKER, 0 MAJOR);
  project-id/path grep 0 hits (g7_s251/README_P2.md). Accepted: public names kept by D-F10-PUBLIC-NAMES (uORB fields
  the scorers key on, XY_P/XY_VP, duplicate multisine), 8 MINORs skipped in S248 (F10_FIX_S248.md) and 11 MINORs of
  S252, all naming or comment only.
- (g) Firmware-only branch from main: PASS, builds px4_sitl_default rc 0 (g7_s251/README_P2.md).
- Review open items: 92 rows closed, justified or superseded (results/g7_s249/REVIEW_ITEMS.md,
  g7_s251/P7A_REVIEW_ROWS.md, report 04_limits 4.6).
Cut items (route_check_247) without code work: listed above or in report 04_limits; G6 item 2 ID-window rescore
dropped (G6 stays NOT PASSED as scored).

## G8 verdict (S257, 2026-11-27): PASSED, with the listed limits
Evidence: `bench/gate_g8.sh`, output `results/g8_s257/gate_g8_out.txt`, 7/7 checks PASS.
- (a) Every gate section has an existing evidence path: PASS, gate_g8.sh check 1; report chapters 01-04, 06, A, g2_margins.
- (b) G1 evidence limits and G3 excluded corners listed: PASS, check 2; `report/04_limits.md` 4.1 (G3), 4.2 (G6).
- (c) Hardware bring-up checklist present: PASS, check 3; `report/06_bringup_checklist.md` (6.7 Unverified lists the open B3-B8 items).
- (d) Errata and history appendix: PASS, check 4; `report/A_history_errata.md`.
- (e) `git diff main -- docs/ko docs/zh docs/uk` empty: PASS, check 5.
- (f) User page in `docs/en` only: PASS, check 6; `docs/en/config_mc/indi_control.md`, links resolve, tables aligned.
- (g) Markdown lint: not applicable, check 7 (no docs make target; prettier not installed offline, manual check done).
Limits:
- Unverified claims: 47 listed (01: 11, 02: 7, 03: 10, 04: 6, 06: 7, A: 5, g2_margins: 1), each marked "Unverified" or
  `[open: ...]` in the chapter text; checked one by one only for 20 (S254, S255), the rest marked in one pass per RC256.
- R1 "refuse to arm without eRPM" is not enforced in firmware (QUESTIONS.md Q36): pending owner Q36, option A
  recommended (reword R1 to "eRPM telemetry required for the validated configuration; without it the modelled actuator
  state runs, not validated"); the bring-up checklist checks telemetry before first flight.
- G3 is NOT PASSED (report 03_validation.md 3.3 with data, 04_limits.md 4.1 limits and corners) and G6 is NOT PASSED
  (03_validation.md 3.6, 04_limits.md 4.2; item 7 un-identified start 6/58 failures, 10 start runs not flown).
- All evidence is simulation only (04_limits.md 4.5); no hardware flight.
Verdict: G8 PASSED with the limits above (unverified-claim count is a tally, results/g8_s257/README.md).
