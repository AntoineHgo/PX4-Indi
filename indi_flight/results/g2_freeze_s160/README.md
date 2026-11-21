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
