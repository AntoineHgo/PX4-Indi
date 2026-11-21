# G4 PID guard, Q20 rule, key 1 (freeze-9, S183 logs, no re-fly)

Rule: GATES.md "Owner amendments S187" first bullet. Narrow-band measure `psd_windows(..., rms_hz=0.5)` (key-2 detector in g3_checks_key2.py,
4 s Hann, 1 s hop, peak bin 20-100 Hz, RMS peak +-2 bins), skipped windows `ta < c+3 and ta+4 > c`, all 4 motors, airborne span as guard_q19.py.
Flagged = ratio > 20 and narrow RMS >= 5e-4. Row INDI values = max narrow-RMS skipped window (all motors). PID ref exists only for
hover_harsh_s1/s2 and cruise_harsh_s1/s2 (g4_pid/); other runs have no PID run and none is checked anyway.

Self-test: `python3 indi_flight/bench/g4_guard_q20_key1.py --selftest` -> selftest OK (known 20 Hz line RMS recovered within 5 %; INDI-only FAIL, shared PASS, >1e-3 FAIL, below-floor not checked).

Command (from indi_flight/results/freeze9_s183):
`python3 ../../bench/g4_guard_q20_key1.py g4/{hover,cruise}_{quiet,typ,harsh}_s{1,2,3} > g4/guard_q20_key1_stdout.txt`

Result: no INDI skipped window is flagged (max narrow RMS 4.839e-04, hover_harsh_s2 17->4#1, below the 5e-4 floor); 14->18 INDI 2.28-2.95e-04 in harsh runs.
INDI/PID narrow RMS at 17->4 (harsh PID pairs): 2.94/3.78, 4.84/4.28, 4.47/3.93, 2.86/3.88 e-04. Pre-look confirmed by computation.

**guard: 0 checked, 0 FAIL**

| run | transition | INDI peak Hz | INDI narrow RMS | INDI ratio | checked | PID peak Hz | PID narrow RMS | PID ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|
| hover_quiet_s1 | 17->4#1 | 22.25 | 1.51e-04 | 7139.5 | no | - | - | - | not checked (no PID ref) |
| hover_quiet_s1 | 4->14#1 | 26.25 | 1.10e-05 | 39.7 | no | - | - | - | not checked (no PID ref) |
| hover_quiet_s1 | 14->18#1 | 39.75 | 9.86e-05 | 104.6 | no | - | - | - | not checked (no PID ref) |
| hover_quiet_s2 | 17->4#1 | 22.25 | 1.63e-04 | 5559.6 | no | - | - | - | not checked (no PID ref) |
| hover_quiet_s2 | 4->14#1 | 20.50 | 1.56e-05 | 73.9 | no | - | - | - | not checked (no PID ref) |
| hover_quiet_s2 | 14->18#1 | 38.00 | 9.44e-05 | 88.5 | no | - | - | - | not checked (no PID ref) |
| hover_quiet_s3 | 17->4#1 | 22.25 | 1.54e-04 | 5259.5 | no | - | - | - | not checked (no PID ref) |
| hover_quiet_s3 | 4->14#1 | 22.50 | 1.70e-05 | 76.8 | no | - | - | - | not checked (no PID ref) |
| hover_quiet_s3 | 14->18#1 | 38.00 | 9.16e-05 | 80.4 | no | - | - | - | not checked (no PID ref) |
| hover_typ_s1 | 17->4#1 | 22.25 | 1.71e-04 | 900.5 | no | - | - | - | not checked (no PID ref) |
| hover_typ_s1 | 4->14#1 | 32.00 | 5.38e-05 | 103.6 | no | - | - | - | not checked (no PID ref) |
| hover_typ_s1 | 14->18#1 | 38.00 | 9.56e-05 | 31.6 | no | - | - | - | not checked (no PID ref) |
| hover_typ_s2 | 17->4#1 | 22.25 | 1.69e-04 | 1346.9 | no | - | - | - | not checked (no PID ref) |
| hover_typ_s2 | 4->14#1 | 70.00 | 5.41e-05 | 138.8 | no | - | - | - | not checked (no PID ref) |
| hover_typ_s2 | 14->18#1 | 90.00 | 1.02e-04 | 33.4 | no | - | - | - | not checked (no PID ref) |
| hover_typ_s3 | 17->4#1 | 22.25 | 1.69e-04 | 1178.9 | no | - | - | - | not checked (no PID ref) |
| hover_typ_s3 | 4->14#1 | 32.00 | 5.69e-05 | 119.2 | no | - | - | - | not checked (no PID ref) |
| hover_typ_s3 | 14->18#1 | 39.75 | 1.23e-04 | 42.9 | no | - | - | - | not checked (no PID ref) |
| hover_harsh_s1 | 17->4#1 | 23.00 | 2.94e-04 | 311.6 | no | 22.25 | 3.78e-04 | 953.4 | not checked |
| hover_harsh_s1 | 4->14#1 | 70.00 | 1.37e-04 | 821.8 | no | 70.00 | 1.01e-04 | 808.8 | not checked |
| hover_harsh_s1 | 14->18#1 | 22.75 | 2.95e-04 | 140.8 | no | 23.50 | 2.29e-04 | 46.7 | not checked |
| hover_harsh_s2 | 17->4#1 | 20.00 | 4.84e-04 | 315.7 | no | 22.25 | 4.28e-04 | 1683.1 | not checked |
| hover_harsh_s2 | 4->14#1 | 70.00 | 1.36e-04 | 890.8 | no | 70.00 | 1.02e-04 | 523.3 | not checked |
| hover_harsh_s2 | 14->18#1 | 22.00 | 2.41e-04 | 75.6 | no | 22.50 | 2.40e-04 | 183.9 | not checked |
| hover_harsh_s3 | 17->4#1 | 20.00 | 2.99e-04 | 150.2 | no | - | - | - | not checked (no PID ref) |
| hover_harsh_s3 | 4->14#1 | 70.00 | 1.38e-04 | 1000.7 | no | - | - | - | not checked (no PID ref) |
| hover_harsh_s3 | 14->18#1 | 22.50 | 2.64e-04 | 145.4 | no | - | - | - | not checked (no PID ref) |
| cruise_quiet_s1 | 17->4#1 | 22.25 | 1.53e-04 | 4062.7 | no | - | - | - | not checked (no PID ref) |
| cruise_quiet_s1 | 4->14#1 | 20.50 | 2.16e-05 | 106.9 | no | - | - | - | not checked (no PID ref) |
| cruise_quiet_s1 | 14->18#1 | 39.75 | 1.00e-04 | 110.7 | no | - | - | - | not checked (no PID ref) |
| cruise_quiet_s2 | 17->4#1 | 22.25 | 1.53e-04 | 8407.3 | no | - | - | - | not checked (no PID ref) |
| cruise_quiet_s2 | 4->14#1 | 21.00 | 1.34e-05 | 90.0 | no | - | - | - | not checked (no PID ref) |
| cruise_quiet_s2 | 14->18#1 | 38.00 | 1.02e-04 | 95.6 | no | - | - | - | not checked (no PID ref) |
| cruise_quiet_s3 | 17->4#1 | 22.25 | 1.49e-04 | 2562.6 | no | - | - | - | not checked (no PID ref) |
| cruise_quiet_s3 | 4->14#1 | 21.25 | 1.46e-05 | 29.2 | no | - | - | - | not checked (no PID ref) |
| cruise_quiet_s3 | 14->18#1 | 38.00 | 1.05e-04 | 92.8 | no | - | - | - | not checked (no PID ref) |
| cruise_typ_s1 | 17->4#1 | 22.25 | 1.59e-04 | 891.8 | no | - | - | - | not checked (no PID ref) |
| cruise_typ_s1 | 4->14#1 | 32.00 | 5.39e-05 | 116.7 | no | - | - | - | not checked (no PID ref) |
| cruise_typ_s1 | 14->18#1 | 87.75 | 1.15e-04 | 30.7 | no | - | - | - | not checked (no PID ref) |
| cruise_typ_s2 | 17->4#1 | 22.25 | 1.77e-04 | 271.4 | no | - | - | - | not checked (no PID ref) |
| cruise_typ_s2 | 4->14#1 | 32.00 | 5.54e-05 | 98.8 | no | - | - | - | not checked (no PID ref) |
| cruise_typ_s2 | 14->18#1 | 38.00 | 1.18e-04 | 52.1 | no | - | - | - | not checked (no PID ref) |
| cruise_typ_s3 | 17->4#1 | 22.25 | 1.87e-04 | 290.8 | no | - | - | - | not checked (no PID ref) |
| cruise_typ_s3 | 4->14#1 | 70.00 | 5.26e-05 | 94.0 | no | - | - | - | not checked (no PID ref) |
| cruise_typ_s3 | 14->18#1 | 87.75 | 1.15e-04 | 30.8 | no | - | - | - | not checked (no PID ref) |
| cruise_harsh_s1 | 17->4#1 | 20.00 | 4.47e-04 | 740.2 | no | 22.25 | 3.93e-04 | 958.1 | not checked |
| cruise_harsh_s1 | 4->14#1 | 70.00 | 1.41e-04 | 894.3 | no | 20.00 | 2.03e-04 | 453.8 | not checked |
| cruise_harsh_s1 | 14->18#1 | 22.75 | 2.28e-04 | 178.9 | no | 22.50 | 2.70e-04 | 289.2 | not checked |
| cruise_harsh_s2 | 17->4#1 | 22.75 | 2.86e-04 | 440.2 | no | 22.25 | 3.88e-04 | 1082.7 | not checked |
| cruise_harsh_s2 | 4->14#1 | 70.00 | 1.39e-04 | 854.9 | no | 70.00 | 1.01e-04 | 724.7 | not checked |
| cruise_harsh_s2 | 14->18#1 | 21.50 | 2.89e-04 | 251.1 | no | 23.75 | 2.13e-04 | 72.7 | not checked |
| cruise_harsh_s3 | 17->4#1 | 23.00 | 2.94e-04 | 305.0 | no | - | - | - | not checked (no PID ref) |
| cruise_harsh_s3 | 4->14#1 | 70.00 | 1.39e-04 | 865.2 | no | - | - | - | not checked (no PID ref) |
| cruise_harsh_s3 | 14->18#1 | 22.00 | 2.71e-04 | 212.2 | no | - | - | - | not checked (no PID ref) |
max INDI narrow RMS over skipped windows: 4.839e-04 (hover_harsh_s2 17->4#1)
guard: 0 checked, 0 FAIL
