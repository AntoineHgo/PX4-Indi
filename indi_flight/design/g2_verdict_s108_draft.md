# G2 verdict draft (S108) - DRAFT, not a decision. GATES.md and results untouched.

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

## 2. Loop-break points with no measurement
- Attitude 267 Hz: S91 roll cell exists but has a hole_report FAIL and no coherence; S107 re-measure did not include 267 Hz. Needs a re-fly with hole check.
- Velocity xy: open (GATES.md row); needs a PINJ_PT 0 xy flight cell plus second key.
- Position xy: open (same); z velocity/position has only prelim PM 57.3 deg (S83), no cross-check stated.
- INDI acceleration z, xy loops: "in work" (T174 S84); stage-output (PINJ_PT 1) cells, second key and model cross-check needed.
- 250 Hz report row (267 Hz) for rate loops: not measured; needs 267 Hz rate cells (analytic only today).
- PID reference path: no measured cell (S91 note: "No measured PID cell exists"); needs M1 gyro-break flights if still required.
- Hole reporter (a15_gaps.py extension): open.

## 3. Verdict paragraph
Met (preliminary pair, pre-freeze): 24 rate cells and 6 attitude cells (800/400 Hz) pass GM >= 6 dB, PM >= 45 deg, DM far above 2 periods; the lowest measured values are yaw meas-torque 400 Hz GM 15.5 dB and attitude roll/pitch PM 56.8 deg / GM 22.0 dB. Model cross-check is met for roll/pitch rate (worst dPM 4.7 deg, dGM 1.86 dB) and the 4 yaw model-only cells; it is NOT met for the 4 yaw measured-torque cells (400 Hz dGM -9.1/-9.7 dB, 800 Hz s2 -3.2 dB, A-39 deferred) nor for attitude GM at 400/267 Hz (+3.4/+4.6 dB, A-36 open; PM explained). Under GATES.md "a margin that passes only because it disagrees with the model is not a pass" these cells are passes with open anomalies, not clean passes. Open: velocity, position, acceleration loops, 267 Hz rows, PID reference, hole reporter. Everything is single-seed in the attitude cells and subject to the stage-6 frozen-pair re-fly (D-G2-DEFER); no G2 gate closure is claimed.

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
