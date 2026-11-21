# S160 G2 freeze cells (D-FREEZE-6 plant), rate loop roll/pitch at 800 and 400 Hz, 3 seeds; fwdef roll 800

Recipe = results/g2_roll_ky20_s138 (S99 injection: MC_INDI_INJ_* lines, axis via INJ_AX 1 roll / 2 pitch) on the freeze
params (results/g5_freeze_s157/params.params, ID_OK 1; params_fwdef = firmware-default cell ID_OK 0, W_MAX 0, ACT_TC
0.05), freeze plant: matched GNSS 110 ms, G4 typical noise (--vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0). hover_long,
quad5in, serial. Post: check_rates.py, pretest_gate.py, m3a_csv.py, m3a_margins_pretest.py (keyed K100/K101).
Commands: pre-test `bash batch.sh` (roll 800/400 s1); rest `bash chain.sh` (also flies the PID g5_events_s1 reference).

| cell | GM dB | PM deg | DM ms | pretest gate |
|---|---|---|---|---|
| roll800_s1 | 19.3 | 56.4 | 47.9 | PASS |
| roll400_s1 | 15.4 | 56.1 | 50.5 | PASS |
Pre-test (2 flights): configuration flies, injection coherent under typical noise, margins script runs. Thresholds
(GM >= 6 dB, PM >= 45 deg, DM >= 2 periods + telemetry latency) met. Remaining cells: chain.sh (batch.log).

## All cells (S160 chain.sh, 15 flights, 0 NO_MARGINS)
| cell | GM dB | PM deg | DM ms | pretest gate |
|---|---|---|---|---|
| roll800 s1/s2/s3 | 19.3/18.8/18.7 | 56.4/56.2/56.5 | 47.9/47.9/48.1 | PASS/PASS/FAIL* |
| roll400 s1/s2/s3 | 15.4/15.5/14.2 | 56.1/55.1/56.1 | 50.5/49.4/51.1 | PASS x3 |
| pitch800 s1/s2/s3 | 18.8/18.6/18.9 | 56.4/56.0/55.9 | 48.2/48.0/47.6 | PASS/PASS/FAIL* |
| pitch400 s1/s2/s3 | 15.1/15.5/15.4 | 55.9/56.0/55.9 | 50.2/50.2/50.2 | FAIL*/PASS/PASS |
| roll800 fwdef s1/s2/s3 (ID_OK 0, W_MAX 0, ACT_TC 0.05) | 15.9/16.4/16.3 | 54.4/54.3/54.3 | 83.5/83.4/83.4 | PASS x3 |
Every cell meets GM >= 6 dB, PM >= 45 deg and DM >= 2 periods + telemetry latency with wide margin; spread over seeds
<= 1.3 dB / 1.1 deg. *pretest_gate FAIL lines are all "hover rate RMS >= 0.02 rad/s" (0.022-0.026): that bound was set at
sim-default noise and the G4 typical profile raises hover rate noise. OPEN (next session): check the GATES G2 validity
text for whether this line invalidates a cell; if it does, re-fly those 3 cells or record a test-defect fix (logged).
Verdicts UNKEYED as a set (scripts keyed K100/K101); att yaw and outer cells not yet flown at the freeze.

## S163: validity of the 3 pretest_gate FAIL cells (open item above, closed)
GATES G2 "Validity of each run" lists: fault == 0, landed == 0, u = c + d, logged rate / holes, injected d = generator.
The pretest_gate hover rate RMS < 0.02 rad/s line is not part of it (it is a pre-test sanity bound set at sim-default
noise). The 3 cells are therefore valid G2 runs; no re-fly, no gate change. The G4 typical profile is judged in G4.

## S163 cells: rate yaw (measured) 800/400 x2, model-only (MC_INDI_W_MAX 0, S100 recipe) roll/pitch/yaw 800/400 x2
`bash batch_s163.sh` (params_yaw.params = params_roll with INJ_AX 3; params_mo_<ax>.params = W_MAX 0). Results below.
- yaw400_s1 (first flight, kept as yaw400_s1_INVALID_simhole/): watchdog tilt > 60 deg at t 42.9 s in hover, BEFORE the
  injection started. Cause: two sim holes (gyro and indi_rate_status frozen ~60 ms at 42.05 s, 88.75 ms at 42.28 s; INDI
  stage cond 0x7f -> 0x7d), produced by an orchestrator post-processing container run in parallel with the flight
  (STATE 4a rule broken). Motors held a stale full-differential command through the 89 ms hole. Invalid run (G2 validity:
  gap > 3 periods), re-flown serially. Cells flown during that window (yaw800_s1, yaw800_s2, yaw400_s2) are hole-checked.
- yaw800_s2 / yaw400_s2 first flights (kept as *_INVALID_holes/): controller holes 17.5 / 22.5 ms, flown while orchestrator
  probe containers ran (06:21-06:23). Re-flown serially 07:03-07:05: yaw400_s2 holes PASS; yaw800_s2 holes OVERALL FAIL
  only on "count-disagree, count-based missing -3" of vehicle_local_position_setpoint (3 EXTRA samples, 0 gaps, max excess
  1.25 ms): not a hole, outer-loop topic, rate-loop topics PASS -> run valid for the rate cell.

### S163 results (table: bench/g2_freeze_table_s163.py -> ../g2_outer_freeze_s163/table_s163.md)
| cells (2 seeds each) | worst PM deg | worst GM dB | worst DM ms | key2 max abs dPM / dGM |
|---|---|---|---|---|
| yaw measured 800 / 400 | 79.0 / 80.8 | 19.8 / 15.3 | 72.8 / 78.7 | 0.4 deg / 0.09 dB |
| model-only roll 800 / 400 | 55.9 / 54.6 | 13.8 / 11.8 | 43.6 / 41.7 | 0.4 / 0.17 |
| model-only pitch 800 / 400 | 55.8 / 54.5 | 13.7 / 12.1 | 43.4 / 41.7 | 0.2 / 0.07 |
| model-only yaw 800 / 400 | 76.1 / 75.4 | 18.0 / 17.0 | 64.2 / 63.6 | 0.1 / 0.12 |
All 16 cells: GM >= 6 dB, PM >= 45 deg, DM >= 2 periods + telemetry latency; 18/18 bins accepted; KEYED by
bench/second_key_m3a_s100.py (independent of m3a_margins_pretest.py; limits 1 dB / 3 deg). With S160 the rate-loop cell
set at the freeze is complete (roll/pitch/yaw x 800/400 x measured/model-only + fwdef roll 800). Still open for the
G2 rate row: linear-model x-check at the freeze params, phase-plateau GM rule (min 1/|L| within 10 deg of -180).
