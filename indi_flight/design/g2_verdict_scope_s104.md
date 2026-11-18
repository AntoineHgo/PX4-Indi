# G2 verdict note scope (S104, read-only)

Scope: prepare the G2 verdict note (measured rate-loop margins cross-checked against the linear model). No
simulations, no edits outside this file.

## 1. GATES.md G2 text and cell table

- G2 heading: GATES.md:103. Thresholds: GM >= 6 dB, PM >= 45 deg, DM >= 2 control periods + telemetry latency
  (model-only: + 0) (GATES.md:123-126).
- Cross-check rule: GATES.md:128-130. Model and measured PM within 10 deg and GM within 3 dB, or the difference
  explained in ANOMALIES.md before use. "A margin that passes only because it disagrees with the model is not a pass."
- Second key: GATES.md:131-132. Disagreement > 1 dB / 3 deg blocks the result.
- Cell table: GATES.md:134-144 (header line 134 onward; rows 140-144):
  - 140 rate roll/pitch/yaw, INDI at M3a: "prelim results 800/400 (stage 2-3, JOURNAL; per-axis table to compile)".
  - 141 attitude: open (break point and second key not yet specified).
  - 142 INDI acceleration z, xy: "in work" (T174 S84).
  - 143 velocity/position z, xy: z prelim PM 57.3 deg (S83); xy open.
  - 144 hole reporter: open.
- Per-cell status (from design-table, not GATES.md): results/g2_rate_table_s99.md is the authoritative per-cell table.
  Counts there: 18 INDI cells + 9 PID cells. PASS (prelim) 6 INDI: roll meas 800; roll model 800/400/267; pitch model
  800; yaw model 800. FAIL 0. NOT COVERED 21 (12 INDI, 9 PID). Gate-required 800+400 INDI cells: 12, of which 5 PASS
  and 7 NOT COVERED. Measured v2 cells at 400/267 and all pitch/yaw measured cells: NOT COVERED.
- Note: GATES.md says the gate is decided on the frozen final pair in stage 6 (GATES.md:105-106). Every S52-S57
  number predates setpoint lead da64bc26b3 (A-34, ANOMALIES.md:25: roll PM 77.5 -> 69 at 800 Hz).

## 2. bench/margins_models.py (T78) and its UNVERIFIED items

- File: bench/margins_models.py (448 lines). Self-test: bench/tests/test_margins_selftest.py, test4_models
  (line 304; compares L_timedomain against analytic L for INDI model-only, INDI meas+blend, and PID; 800 and 400 Hz).
  Note: the test file's header says it tests margins_est.py; test4 is the only test here that exercises margins_models.
- Loops modelled: L_indi (INDI rate loop, M3a break, line 81), L_pid (PID rate loop, line 120), attitude loop
  L_att_indi / L_att_pid (lines 158, 192, rate-setpoint break, roll/pitch only, yaw not modelled), outer-loop factor
  (lines 177-187), continuous-time variants L_indi_cont / L_pid_cont (lines 225-229), and a time-domain simulator
  simulate_loop (line 298) with L_timedomain (line 364).
- CLI: `python3 margins_models.py <out_dir>` (main, line 435; argparse at 436-446). Writes a1_prediction.md and
  margins_models_table.md. The module docstring (lines 1-24) gives the recursions and parameters.
- Defaults: INDI_DEF at lines 36-38 (lat=0 at line 37, tau_r 0.033, tau_m 0.02, d_m 0). PID_DEF at line 46 (lat=0).
- The literal string "T78 UNVERIFIED" does not appear in any file. The only UNVERIFIED wording is in the
  alpha_coef docstring (line 60: "read from memory, see UNVERIFIED in the summary"), and the referenced summary
  was not found. The JOURNAL entry for S38 (JOURNAL.md:188) and the T78 row (JOURNAL.md:305) say self-test 4 passed.
  The UNVERIFIED list below is therefore reconstructed from the code and the docstring, not from a source list.

| # | Item | Where in the code | Verifying source (PX4 under src/) | Status |
|---|---|---|---|---|
| a | AlphaFilter coefficient alpha = Ts/(Ts+tau), tau = 1/(2 pi fc) | margins_models.py:59-62 (alpha_coef), used by tf_alpha 70 | src/lib/mathlib/math/filter/AlphaFilter.hpp: setCutoffFreq at lines 90-101 calls setParameters(1/fs, 1/(2 pi fc)) (verified). The alpha formula inside setParameters was NOT read. | Partly verified; read setParameters before closing |
| b | LPF2p (bilinear Butterworth) coefficients | margins_models.py:50-57 (lpf2p_ba) | src/lib/mathlib/math/filter/LowPassFilter2p.hpp:78-86: c = 1 + 2 cos(pi/4) ohm + ohm^2, b0 = ohm^2/c, a1 = 2(ohm^2-1)/c, a2 = (1-2cos(pi/4)ohm+ohm^2)/c. Matches the model. The definition of fr / ohm = tan(pi fc/fs) at line 77-78 was seen only as tanf(M_PI_F/fr) and fr was NOT read. | Matches; confirm fr = fs/fc |
| c | gz / ESC latency = 0 | margins_models.py:37 and 46 (lat=0 default, INDI_DEF and PID_DEF) | Latency lives in the real chain: src/modules/simulation/gz_bridge/GZMixingInterfaceESC.cpp (not read) and the actuator_motors output path in src/modules/mc_rate_control or the mixing output. stage2_margins_s35.md:103 names "gz command latency" in A_r, so the model's zero latency is a stated simplification. | Open: the sim latency value is not measured in any file read |
| d | Measured path = eta x motor state (meas=True model) | margins_models.py:20-22 (docstring: t_f_meas = H z^-n (eta m)); meas parameter at line 37 | Firmware: src/modules/mc_indi_rate_control (measured torque, MC_INDI_W_MAX, per the S100 README). Also the sim proxy at run_scenario.py:806 (UNVERIFIED that it scales all motors, stage2_margins_s35.md:141). | Open: eta proxy not verified |
| e | Yaw | margins_models.py:162 ("yaw is not modelled") and the att loop L_att_indi (roll/pitch only) | src/modules/mc_att_control or the yaw weight in src/modules/mc_att_control/AttitudeControl (not read). | Open: yaw model absent; yaw cells in G2 compare to a model that does not exist |
| f | Attitude loop model (T194, att_p 8 HEAD_FLIGHT, att_lat 1, sp_lead) | margins_models.py:44 (HEAD_FLIGHT), 141-196 | src/modules/mc_att_control and src/modules/mc_rate_control setpoint lead (commit da64bc26b3). Gain value (att_p) is UNVERIFIED (stage2_margins_s35.md:128). | Open: gain value; design note and second key not yet written (GATES.md:141) |
| g | 267 Hz analytic only | margins_models.py: fs parameter default 800.0 (line 81 and onward); no 267 Hz self-test | Measured 267 Hz cells are NOT COVERED (results/g2_rate_table_s99.md). The only 267 Hz model numbers are the S57 analytic prediction 10.2/10.0 dB, 83.2/83.6 deg (table row roll_m3a_267b). | Analytic only, no measured 267 Hz comparison exists |

- Verified against the journal: T78 self-test 4 ALL PASS, break-checked (JOURNAL.md:188).
- Model-vs-measured disagreement on record (see section 4): the S41 comparison (results/stage2_s41/a21_model_vs_measured.md)
  found the as-coded INDI model PM 42.7 deg @3.25 Hz versus measured PM 24.0-25.3 deg @4.5-4.75 Hz; GM 6.1 dB versus
  4.3-6.0 dB. That is a model-vs-measurement gap larger than the G2 10 deg / 3 dB tolerance, and it predates the
  S100 model-only cells. The S100 model-only cells (PM 72-91 deg, different lead and parameter set from S38) are not yet reconciled with the S38 model prediction
  (42.7 deg, JOURNAL.md:188), so the cross-check is currently unresolved.

## 3. Measured INDI v2 rate-cell results

- Model-only (no telemetry, `--sim v2` with CA_R_W_MAX 0 so MC_INDI_W_MAX 0): results/g2_rate_modelonly_s100/.
  Per-cell GM/PM/DM (primary and second key) are in results/g2_rate_modelonly_s100/key_k101/summary.md (K101, 12 cells,
  12/12 AGREE). Worst over the 12 cells (primary): GM 10.12 dB (roll400_s2), PM 70.8 deg (pitch400_s2), DM 39.7 ms
  (pitch400_s2). Second-key worst: GM 10.14, PM 70.53 (pitch400_s2), DM 39.51 ms. All clear 6 dB / 45 deg / 2 periods.
  Note: the 12-cell table is taken as written from the K101 summary. Its mapping to the S100 README (which lists only P400 and Y800) was NOT checked.
  covers the batch cells (pitch/roll/yaw at 400 and 800, seeds 1-2) plus P400 and Y800. Per-cell margins.txt files are under each cell dir.
- Measured-telemetry cells (`--sim v2` with the rotor speed path): the only grep hits for K101/S101 are
  results/g2_rate_table_s99.md and results/g2_rate_modelonly_s100/. No per-cell measured-telemetry margins file for
  K101/S101 exists. The measured-path numbers that do exist are in results/g2_rate_table_s99.md:
  - roll 800 measured v2 (S57 firmware): GM 16.6/16.3, PM 77.5/77.0, DM 70/72 ms, 2 seeds (stage3_s57/roll_m3a_meas800).
  - roll 800 measured v2 (HEAD S76/S77): GM 16.2, PM 69.1, DM 47 ms, 1 seed. Worst measured value; A-34 open.
  - roll 400, pitch 800/400/267, yaw 800/400/267 measured v2: NOT COVERED (no data).
- Worst across all PASS INDI cells (prelim): PM 69.1 deg (roll 800 measured HEAD). GM worst 10.0 dB (roll 267 model).

## 4. Existing model-vs-measured comparisons

Hits from grep -rln 'model.*measured\|cross-check' design/ results/ (first 20):
- results/stage2_s41/a21_model_vs_measured.md: A-21 closing test, INDI model-only roll loop, model vs measured (S41).
  Result: model PM 42.7 deg @3.25 Hz, GM 6.1 dB; measured PM 24.0-25.3 deg @4.5-4.75 Hz, GM 4.3-6.0 dB. A gap of
  about 18 deg PM, larger than the G2 10 deg tolerance. This is the most directly relevant file. Its scripts are
  bench/a21_compare_s41.py and bench/a21_extra_fits_s41.py. The S41 measurements (seed 2, S40 pretest) predate the S100 model-only cells.
- bench/att_model_vs_measured.py and design/t194_att_model_log.md: attitude-loop model vs measured (T194).
- results/stage3_s78_a34/compare.py and README.md: A-34 (HEAD roll PM drop) comparison.
- design/route_check_79.md, route_check_103.md, design/attitude_break_s86.md, design/rate_lead_note.md, design/stage2_margins_s35.md: notes that describe the model-measured cross-check plan.
- No file found that reports a G2 PASS/FAIL cross-check of the S100 model-only cells against bench/margins_models.py.
  The S100 cells were checked by second key (K101), not against the linear model. That is a gap for the G2 cross-check rule.

## 5. Proposed task list for the G2 verdict note (max 6)

1. Build the per-cell G2 table: inputs results/g2_rate_table_s99.md, results/g2_rate_modelonly_s100/key_k101/summary.md,
   the cell margins.txt files. Output: a table in the verdict note with one row per cell, status and source. Size: 2-3 tool calls.
2. Reproduce the linear model: run `python3 bench/margins_models.py <scratch dir>` and `python3 bench/tests/test_margins_selftest.py`
   (offline, no sim). Input: bench/margins_models.py, bench/margins_est.py. Output: a1_prediction.md and models table at the
   G2 configs (800, 400, 267 Hz; model-only and meas). Size: 2-3 tool calls.
3. Reconcile the A-21 gap: read results/stage2_s41/a21_model_vs_measured.md and bench/a21_compare_s41.py. Decide whether
   the 18 deg PM gap is explained (ANOMALIES.md) or still open, which G2 cross-check requires before a result is used.
   Size: 2-4 tool calls.
4. Verify the unverified PX4 inputs: read src/lib/mathlib/math/filter/AlphaFilter.hpp setParameters (alpha formula), the
   fr definition in src/lib/mathlib/math/filter/LowPassFilter2p.hpp (lines 70-80), and the gz/ESC latency path
   (GZMixingInterfaceESC.cpp). Size: 3 tool calls.
5. Model-vs-measured cross-check table: for each PASS cell, |PM_meas - PM_model| and |GM_meas - GM_model|, flagged against
   10 deg / 3 dB (GATES.md:128-130). Input: items 1-2 outputs. Size: 2-3 tool calls.
6. Write the G2 verdict note (design/g2_verdict_*.md, not this scoping file). Mark the 21 NOT COVERED cells and the
   yaw / attitude / 267 measured cells as open, with the decision pending stage 6 frozen pair. Size: 2 tool calls.

## 6. Summary and unverified items

1. G2 text: GATES.md:103-144. Thresholds GM >= 6 dB, PM >= 45 deg, DM >= 2 periods; cross-check PM 10 deg, GM 3 dB (l.128-130).
2. Cell table: 6 prelim PASS INDI cells, 0 FAIL, 21 NOT COVERED (results/g2_rate_table_s99.md). Worst PM 69.1 deg (roll 800 measured HEAD).
3. Model: bench/margins_models.py models INDI, PID, attitude, and time-domain loops; self-test 4 passes; yaw and 267 Hz
   measured are not modelled. Latency = 0 is a simplification (margins_models.py:37).
4. Cross-check: A-21 (S41) shows a model-vs-measured PM gap of about 18 deg, which exceeds the G2 tolerance and is unresolved.
   No G2 cross-check of the S100 model-only cells against the linear model exists.
5. Unverified / not done: the "T78 UNVERIFIED" list as a literal document was not found; the AlphaFilter setParameters alpha
   formula, the LPF2p fr definition, the gz/ESC latency value, and the eta x motor-state proxy were not read in full;
   no per-cell measured-telemetry (K101/S101) margins file was found; the S100 model-only numbers were taken from the
   K101 summary, not recomputed.
