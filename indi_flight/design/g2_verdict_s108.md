# G2 verdict note (S108, reviewed by the orchestrator; drafted S107 by D107)

S108 review: sections 1 and 4 kept as drafted; section 2 and the verdict paragraph were WRONG on the outer loops
(draft searched only the S84 table). Corrected below. Applied to GATES.md G2 cell table (S108).

## 0. S108 corrections (orchestrator, from result READMEs)
- Outer loops WERE flown: results/stage5_s86_g2outer/README.md (z: accel break pt1 4 cells PM 58.3-63.7 deg, S88
  re-fly of r800_s2 59.6; vel/pos break pt0 4 cells PM 57.3-66.1 incl. S83 r400_s1) and results/stage5_s87_xy/README.md
  (16 xy cells, PM 49.7-64.8, GM 18.2-19.3 dB, DM >= 0.43 s, coherence >= 0.93, hole_report pass after re-fly and
  D-HOLE-EXCESS). All >= thresholds, 2 seeds. Margins not second-keyed (T183 keyed the xy FRF of one cell pair only).
  No linear model cross-check exists for velocity, position or acceleration loops.
- Hole reporter is done (bench/hole_report.py, frozen S89), not open.
- Attitude cells are one seed; the gate asks the worst of 2 runs. Not re-flown now: every cell is re-flown on the
  frozen pair at stage 6 (D-G2-DEFER), so a second seed of a pre-freeze pair buys no gate evidence (RC108 amendment).
- Remaining work before the stage-6 G2 run (tooling, offline): outer-cell margin second key; linear outer-loop
  model; A-36 and A-39 explained or bounded; 267 Hz rows; serial flights only.

Sources: GATES.md:103-144, design/g2_verdict_rate_s105.md, design/g2_yaw_crosscheck_s107.md,
results/g2_attbreak_s107/README.md, results/stage5_s91_attbreak/model_vs_measured.md, ANOMALIES.md A-36 / A-39.
All rows preliminary (pre-freeze pair); final table at stage-6 freeze (D-G2-DEFER).

## 1. Proposed replacement rows for the GATES.md G2 cell table
Columns as existing (loop | break point | INDI injector | status), status split into measured / cross-check / evidence / commit.

| loop | break point | INDI injector | status (S108 draft, preliminary) |
|---|---|---|---|
| rate roll, pitch (800, 400 Hz; v2 measured and model-only torque; 16 cells) | M3a torque setpoint | MC_INDI_INJ_* (D-G2-INJ) | measured: all PASS. Cross-check: YES, all within tolerance, worst dPM 4.7 deg, dGM 1.86 dB. Evidence: design/g2_verdict_rate_s105.md, results/g2_rate_table_s99.md, design/g2_crosscheck_s105.md. Commit 7aa00e20da. 267 Hz: not measured |
| rate yaw (800, 400 Hz; both paths; 8 cells) | M3a torque setpoint | MC_INDI_INJ_* | measured: all PASS (meas-path GM 15.5-21.5 dB; table in yaw note). Cross-check: PARTIAL, A-39. Model-only 4/4 within tolerance (dGM <= 0.96 dB, dPM +6.4..+7.4 deg). Measured-torque 800 Hz: dGM -2.94 (s1) in, -3.20 (s2) out by 0.2 dB. Measured-torque 400 Hz: dGM -9.73/-9.06 out (tol 3), cause open. PM +6.4..+8.2 deg above model in all 8 (in tol, cause open). Evidence: design/g2_yaw_crosscheck_s107.md. Commit fb96c31211 |
| attitude (800, 400 Hz roll/pitch/yaw) | attitude-loop output (rate setpoint) | MC_INDI_INJ_PT 1 | measured at HEAD bf6c1127e6: 6/6 PASS (PM 56.8-73.5 deg, GM 22.0-34.4 dB except yaw 800 32.1 dB, DM 0.118-0.449 s). Cross-check: PARTIAL, A-36. Roll/pitch PM explained by outer-loop factor (dPM +0.2/-0.3 deg, keyed T195); GM: model 1.6-4.6 dB below measured at 800/400/267 (800 Hz 1.6 pass; 400 Hz 3.4 and 267 Hz 4.6 exceed 3 dB, model conservative); yaw attitude not modelled. Evidence: results/g2_attbreak_s107/README.md, results/stage5_s91_attbreak/model_vs_measured.md. Commit 8ec7d4a95b (S107), S91 model note 2ded732f64 |

## 2. Loop-break points with no measurement (DRAFT TEXT, superseded by section 0 for velocity/position/accel and hole reporter)
- Attitude 267 Hz: S91 roll cell exists but has a hole_report FAIL and no coherence; S107 re-measure did not include 267 Hz. Needs a re-fly with hole check.
- Velocity xy: open (GATES.md row); needs a PINJ_PT 0 xy flight cell plus second key.
- Position xy: open (same); z velocity/position has only prelim PM 57.3 deg (S83), no cross-check stated.
- INDI acceleration z, xy loops: "in work" (T174 S84); stage-output (PINJ_PT 1) cells, second key and model cross-check needed.
- 250 Hz report row (267 Hz) for rate loops: not measured; needs 267 Hz rate cells (analytic only today).
- PID reference path: no measured cell (S91 note: "No measured PID cell exists"); needs M1 gyro-break flights if still required.
- Hole reporter (a15_gaps.py extension): open.

## 3. Verdict paragraph
Met (preliminary pair, pre-freeze): 24 rate cells and 6 attitude cells (800/400 Hz) pass GM >= 6 dB, PM >= 45 deg, DM far above 2 periods; the lowest measured values are yaw meas-torque 400 Hz GM 15.5 dB and attitude roll/pitch PM 56.8 deg / GM 22.0 dB. Model cross-check is met for roll/pitch rate (worst dPM 4.7 deg, dGM 1.86 dB) and the 4 yaw model-only cells; it is NOT met for the 4 yaw measured-torque cells (400 Hz dGM -9.1/-9.7 dB, 800 Hz s2 -3.2 dB, A-39 deferred) nor for attitude GM at 400/267 Hz (+3.4/+4.6 dB, A-36 open; PM explained). Under GATES.md "a margin that passes only because it disagrees with the model is not a pass" these cells are passes with open anomalies, not clean passes. Outer loops (S83/S86/S87, 24 cells) pass with PM >= 49.7 deg and GM >= 18.2 dB, unkeyed and without model cross-check. Open: outer margin key and model, 267 Hz rows, PID reference. Everything is single-seed in the attitude cells and subject to the stage-6 frozen-pair re-fly (D-G2-DEFER); no G2 gate closure is claimed.

## 4. UNVERIFIED
- Yaw meas-torque GM 21.53/21.27 (800), 15.5/16.17 (400): read from the yaw note's table; underlying g2_rate_batch_s99 README not opened.
- "24 cells all PASS", roll/pitch worst dPM 4.7/dGM 1.86: taken from the S105 note, not recomputed.
- Attitude yaw 400/800 not modelled (S91 note); whether S107 changed that: not checked.
- Attitude 800 Hz dGM 1.6 uses the S93 T195 model with stock outer-loop defaults; not re-run at HEAD (D-RATE-LEAD changed after S91).
- Velocity/position/accel-INDI status taken from the S84 GATES table only; later progress (S85-S107) not searched.
- Whether second keys exist for the S107 attitude cells: not stated in the README.
- Commit ids: 7aa00e20da, fb96c31211, 8ec7d4a95b, 2ded732f64 are the latest commits touching the paths, not verified as the evidence-creating commits of every file.
- S107 attitude README "coherence not recomputed; one seed".
- A-39 causes (eRPM timing, IMU 800 vs model 400 filters) and J_r/w_h inputs are unverified per the yaw note.
- Whether a G2 margin pass counts "worst of 2 runs" for attitude cells (S107 is one seed): requirement vs. evidence mismatch.
