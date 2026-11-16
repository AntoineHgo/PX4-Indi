# Stage-2 loop-margin summary (S49)

Compiled from existing result files only. No simulation, no code change. Numbers quoted as they appear in the files.
Status key: valid = usable for G2; VOID = not usable (reason given); model-only = model script output, not a flight.
Airframe for all INDI rows: quad5in (reference airframe). No x500 margin number exists in the stage-2 results (see gaps).

## 1. Configuration rows

| airframe | controller | loop / break point | config (K_R, ACT_TC, MC_ROLL_P, rate Hz, path) | source | PM deg @ f_c Hz | GM dB @ Hz | DM ms | status | file |
|---|---|---|---|---|---|---|---|---|---|
| quad5in | INDI | roll rate, M3a torque-setpoint break (`MC_INDI_INJ_AX 1`) | K_R 20, ACT_TC 0.02, MC_ROLL_P 8, 800 Hz, model-only path, AMP 0.001, G1_R 1757, G2_Y 27, seed 1 | model-only flight `results/stage2_s47/roll_m3a/model_g2_a001/` | 22.3 @ 3.48 | 4.1 @ 5.64 | 17.9 | valid (model-only path, per task brief; pretest_gate rc 1 from window overlap with injection) | `results/stage2_s47/roll_m3a/README.md` ("Follow-up S47", `model_g2_a001_margins.txt`); `results/stage2_s48/README.md` sect. 1 |
| quad5in | INDI | roll rate, M3a torque-setpoint break | K_R 20, ACT_TC 0.033, MC_ROLL_P 8 (README; not in `tc33_p8.params`, UNVERIFIED), rate UNVERIFIED, model-only path, AMP 0.001, seed 1, speed 4 | measured flight `results/stage2_s48/m3a_check/tc33_p8/` (margins `tc33_p8_margins.txt`) | 25.9 @ 2.92 (file: 25.87 @ 2.923) | 10.7 @ 7.56 (file: 10.75 @ 7.556) | 24.6 (file: 0.02458 s) | valid | `results/stage2_s48/README.md` sect. 4; `results/stage2_s48/m3a_check/tc33_p8_margins.txt` |
| quad5in | INDI | roll rate, M3a torque-setpoint break | K_R 20, ACT_TC 0.033, MC_ROLL_P 3 (confirmed in run.json per README; `tc33_p3.params` has `MC_ROLL_P 3.0`), rate UNVERIFIED, model-only path, AMP 0.001, seed 1, speed 4 | measured flight `results/stage2_s48/m3a_check/tc33_p3/` (margins `tc33_p3_margins.txt`) | 42.9 @ 2.79 (file: 42.85 @ 2.790) | 13.4 @ 8.72 (file: 13.39 @ 8.723) | 42.7 (file: 0.04267 s) | valid; best valid roll PM, still below G2 PM >= 45 | `results/stage2_s48/README.md` sect. 4; `results/stage2_s48/m3a_check/tc33_p3_margins.txt` |
| quad5in | INDI | roll rate, M3a | K_R 20, ACT_TC 0.02, MC_ROLL_P 8, 800 Hz, model-only, AMP 0.005, G1 1757 | `results/stage2_s47/roll_m3a/model_s1/` (`model_s1_margins.txt`) | 32.4 @ 3.81 | 6.69 @ 8.61 | 23.6 | VOID: AMP 0.005 on a saturating plant (motor pin 0.26, pretest_gate FAIL) | `results/stage2_s47/roll_m3a/README.md` table |
| quad5in | INDI | roll rate, M3a (S40 model-only) | S40 AMP 0.005, seed 1 | `results/stage2_s40/pretest_inj/` | 25.3 (S40 README) | 4.3 | 16 | VOID: S40-S43 in A-23 17 Hz limit cycle (STATE.md) | `results/stage2_s40/pretest_inj/README.md` line 68 |
| quad5in | INDI | roll rate, M3a (S40 measured preliminary) | S40 measured, 800 Hz | `results/stage2_s40/pretest_inj/margins_measured_long.txt` (per README) | 61.4 | 12.2 | 35 | VOID: A-23 limit cycle (STATE.md) | `results/stage2_s40/pretest_inj/README.md` line 67 |
| quad5in | INDI | roll rate, M3a (S41 model-only, seed 2) | AMP 0.005, seed 2, hover_long, speed 4 | `results/stage2_s41/model_long_s2/` (`margins_model_long_s2.txt`) | 24.0 @ 4.75 | 6.0 @ 7.66 | 14 | VOID: A-23 limit cycle (STATE.md); 14/18 bins | `results/stage2_s41/README.md` |
| quad5in | INDI | roll rate, model (att loop closed, S47 check) | K_R 20, ACT_TC 0.02, MC_ROLL_P 8, model | `att_loop_model.md` (S47 measured row compared) | 23.6 @ 3.48 | 4.7 | 18.8 | model-only | `results/stage2_s48/att_loop_model.md` line 31-32 |
| quad5in | INDI | roll rate, model (K20 P8 ACT_TC matched) | K_R 20, ACT_TC 0.033, P_att 8, model | `att_loop_model.md` / `lead_model.md` | 28.6 @ 2.97 | 14.2 | 26.8 | model-only | `results/stage2_s48/att_loop_model.md` line 32; `results/stage2_s48/README.md` sect. 2 |
| quad5in | INDI | roll rate, model (K20 P3, ACT_TC 0.033) | K_R 20, ACT_TC 0.033, P_att 3, model | `att_loop_model.md` line 33 | 35.2 @ 3.31 | 5.6 | 29.6 | model-only | `results/stage2_s48/att_loop_model.md` line 33 (ACT_TC of this row: UNVERIFIED, table has 0.02 baseline) |
| quad5in | INDI | roll rate, model, rate-only (no attitude P) | K_R 20, ACT_TC 0.02, model | `att_loop_model.md` line 30 | 42.7 @ 3.25 | 6.1 | 36.5 | model-only | `results/stage2_s48/att_loop_model.md` line 30 |
| quad5in | INDI | roll rate, candidate lead (rate-prediction, tau_c 0.033) | K_R 20, P_att 8, 800 Hz, model | `lead_model.md` | 60.8 @ 3.02 | 16.3 | 55.8 | model-only, stage-3 candidate, not flown | `results/stage2_s48/lead_model.md` row "INDI K20 tau_c 0.033 P8" |
| quad5in | INDI | roll rate, candidate lead | K_R 40 (K40), tau_c 0.033, P_att 8, 800 Hz, model | `lead_model.md` | 56.0 @ 6.65 | 10.7 | 23.4 | model-only, stage-3 candidate, not flown | `results/stage2_s48/lead_model.md` row "INDI K40 tau_c 0.033 P8" |
| quad5in | INDI | roll rate, candidate lead | K40, tau_c 0.033, P_att 8, 400 Hz, model | `lead_model.md` | 53.0 @ 6.72 | 9.6 | 21.9 | model-only | `results/stage2_s48/lead_model.md` row "INDI fs400 K40 tau_c 0.033 P8" |
| quad5in | INDI | roll rate, candidate lead | K40, tau_c 0.033, P_att 8, 250 Hz label, model | `lead_model.md` | 49.6 @ 6.80 | 8.6 | 20.3 | model-only; label "fs250" may really be 267 Hz (design/stage2_margins_s35.md sect. 0, UNVERIFIED for this run) | `results/stage2_s48/lead_model.md` row "INDI fs250 K40 tau_c 0.033 P8" |
| quad5in | PID | roll rate, model (airframe gains, G1 1757) | PID airframe gains (control-type value not stated in file, UNVERIFIED), P 8, model | `lead_model.md` | 42.9 @ 6.63 | -25.8 (sign as written; UNVERIFIED) | 18.0 | model-only | `results/stage2_s48/lead_model.md` row 1; `results/stage2_s48/README.md` sect. 2 |
| quad5in | PID | roll rate, model (P 5) | MC_ROLL_P 5, model | `lead_model.md` | 45.1 @ 6.78 | -28.3 (sign as written; UNVERIFIED) | 18.5 | model-only | `results/stage2_s48/lead_model.md` row 2 |
| quad5in | PID | any loop, measured | none found | - | - | - | - | NOT FOUND | - |
| x500 | PID | any | none found | - | - | - | - | NOT FOUND | - |
| x500 | INDI | any | none found | - | - | - | - | NOT FOUND | - |

Notes:
- MC_RATE_CTL_TYPE is 1 in all S47/S48 INDI params files (`tc33_p8.params`, `tc33_p3.params`). PID model rows in `lead_model.md` are PID by name; the PID control type value is not in the files read here (UNVERIFIED).
- x500: stage-2 runs in S40-S47 failed or were never run on x500 (`results/stage2_s40/pretest_inj/README.md`: `--sim v2` raises SystemExit for non-x500 models; `No model named <x500_0>` in several `gz_model_info.txt`). No x500 margin number exists in these results.

## 2. Model vs measured (rows with both)

| airframe | controller | loop | config | measured PM / GM / DM (file) | model PM / GM / DM (file) | PM diff | GM diff | DM diff | status |
|---|---|---|---|---|---|---|---|---|---|
| quad5in | INDI | roll rate M3a | ACT_TC 0.02, K20 P8, AMP 0.001 | 22.3 @ 3.48 / 4.1 @ 5.64 / 17.9 (S47 `model_g2_a001_margins.txt`) | 23.6 @ 3.48 / 4.7 / 18.8 (`att_loop_model.md` line 31) | +1.3 | +0.6 | +0.9 | valid |
| quad5in | INDI | roll rate M3a | ACT_TC 0.033, P8, AMP 0.001 | 25.9 @ 2.92 / 10.7 @ 7.56 / 24.6 (S48 `tc33_p8_margins.txt`) | 28.6 @ 2.97 / 14.2 @ 8.6 / 26.8 (S48 README sect. 4) | +2.7 | +3.5 | +2.2 | valid |
| quad5in | INDI | roll rate M3a | ACT_TC 0.033, P3, AMP 0.001 | 42.9 @ 2.79 / 13.4 @ 8.72 / 42.7 (S48 `tc33_p3_margins.txt`) | 43.8 @ 2.81 / 15.7 / 43.3 (S48 README sect. 4) | +0.9 | +2.3 | +0.6 | valid |

Differences are computed here only to show the spread quoted in S48 README ("within 3 deg / 0.05 Hz / 2.2 ms; GM optimistic by 2.3-3.5 dB"). They are not new results. The GM and PM differences are simple subtractions of the quoted numbers.

## 3. Gaps: G2 break points without a valid number

Break points: rate x3 (roll, pitch, yaw), attitude, velocity, position, INDI accel; rates 800 / 400 / 250 Hz.

- Rate roll, INDI, 800 Hz: valid measured-path rows exist (S48 `tc33_p8`, `tc33_p3`). Best PM 42.9 deg, below G2 PM >= 45. Only one rate (800 Hz) is measured.
- Rate roll, INDI, 400 Hz and 250 Hz: model only (`lead_model.md`). No valid measured number.
- Rate pitch, INDI: no M3a margin in any stage-2 folder read.
- Rate yaw, INDI: no valid number. S47 yaw spin-up G2_Y 27 test is a rate-noise test, not a margin (`results/stage2_s47/roll_m3a/README.md`).
- Rate roll/pitch/yaw, PID: model only (roll, P 8 and P 5 in `lead_model.md`). No measured PID margin. Pitch and yaw PID: nothing found.
- Attitude loop: model only (`att_loop_model.md` "+att P8" column). No measured attitude-break margin.
- Velocity loop: nothing found.
- Position loop: nothing found.
- INDI accel loop: nothing found (M3b break in `design/stage2_margins_s35.md` sect. 1.2 not run in the folders read).
- x500 (any loop, PID or INDI): nothing found.

## 4. Numbers not traced to a file

- None of the numbers in this table was left untraced. Caveats: PID GM values in `lead_model.md` are negative (-25.8, -28.3) as written in the file; their meaning was not checked (UNVERIFIED). The MC_ROLL_P 8 and K_R 20 of the flights are from the README, not from the params (UNVERIFIED, see row notes). The S48 rate of the flights (800 Hz) is not stated in the README (UNVERIFIED).

## Orchestrator note (S49)
- PID model GM -25.8 / -28.3 dB (from `lead_model.md`) are not read as margins: a negative GM from a phase crossing
  below crossover means a low-frequency -180 deg crossing (conditionally stable shape) or a script sign convention.
  Not checked; PID measured margins on quad5in are a G2 reference still to fly (F-5). Do not quote these two values.
- Missing for G2: every break point except INDI roll at the torque break (800 Hz); no 400/250 Hz rows; no measured PID.
