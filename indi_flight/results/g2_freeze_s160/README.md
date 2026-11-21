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
