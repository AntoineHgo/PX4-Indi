# G4 PID guard Q20, key 2 (freeze-9, no re-fly)

Command (from `indi_flight/`; args are `g4/<run>,g4_pid/<run>` where a PID reference exists, else `g4/<run>,-`):
```
python3 bench/g4_guard_q20_key2.py --selftest   # 9/9 PASS
python3 bench/g4_guard_q20_key2.py results/freeze9_s183/g4/<run>,results/freeze9_s183/g4_pid/<run> ... (18 runs) > results/freeze9_s183/g4/guard_q20_key2_stdout.txt
```
Rule: Q20 (GATES.md S187 first bullet). Transitions = vehicle_status nav_state changes inside the airborne span; windows `ta < c+3 and ta+4 > c`, 4 motors, `psd_windows(rms_hz=0.5)`. INDI value = flagged window of largest RMS if any, else largest-RMS skipped window (motor m). PID value = PID largest-RMS skipped window of the same transition (nearest-to-INDI-line window used for the shared test, any motor). Checked = ratio > 20 and RMS >= 5e-4.

| run | transition | c s | INDI Hz | INDI narrow RMS | INDI ratio | motor | checked | PID Hz | PID RMS | PID ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| hover_quiet_s1 | 17->4 | 37.3 | 22.25 | 1.51e-04 | 7139.5 | 2 | not checked | n/a | n/a | n/a | not checked |
| hover_quiet_s1 | 4->14 | 52.0 | 26.25 | 1.10e-05 | 39.7 | 1 | not checked | n/a | n/a | n/a | not checked |
| hover_quiet_s1 | 14->18 | 119.2 | 39.75 | 9.86e-05 | 104.6 | 3 | not checked | n/a | n/a | n/a | not checked |
| hover_quiet_s2 | 17->4 | 37.2 | 22.25 | 1.63e-04 | 5559.6 | 1 | not checked | n/a | n/a | n/a | not checked |
| hover_quiet_s2 | 4->14 | 52.0 | 20.50 | 1.56e-05 | 73.9 | 0 | not checked | n/a | n/a | n/a | not checked |
| hover_quiet_s2 | 14->18 | 119.3 | 38.00 | 9.44e-05 | 88.5 | 2 | not checked | n/a | n/a | n/a | not checked |
| hover_quiet_s3 | 17->4 | 37.2 | 22.25 | 1.54e-04 | 5259.5 | 2 | not checked | n/a | n/a | n/a | not checked |
| hover_quiet_s3 | 4->14 | 52.0 | 22.50 | 1.70e-05 | 76.8 | 1 | not checked | n/a | n/a | n/a | not checked |
| hover_quiet_s3 | 14->18 | 119.0 | 38.00 | 9.16e-05 | 80.4 | 3 | not checked | n/a | n/a | n/a | not checked |
| hover_typ_s1 | 17->4 | 37.2 | 22.25 | 1.71e-04 | 900.5 | 3 | not checked | n/a | n/a | n/a | not checked |
| hover_typ_s1 | 4->14 | 52.0 | 32.00 | 5.38e-05 | 103.6 | 3 | not checked | n/a | n/a | n/a | not checked |
| hover_typ_s1 | 14->18 | 119.0 | 38.00 | 9.56e-05 | 31.6 | 3 | not checked | n/a | n/a | n/a | not checked |
| hover_typ_s2 | 17->4 | 37.2 | 22.25 | 1.69e-04 | 1346.9 | 0 | not checked | n/a | n/a | n/a | not checked |
| hover_typ_s2 | 4->14 | 52.0 | 70.00 | 5.41e-05 | 138.8 | 1 | not checked | n/a | n/a | n/a | not checked |
| hover_typ_s2 | 14->18 | 120.0 | 90.00 | 1.02e-04 | 33.4 | 0 | not checked | n/a | n/a | n/a | not checked |
| hover_typ_s3 | 17->4 | 37.2 | 22.25 | 1.69e-04 | 1178.9 | 2 | not checked | n/a | n/a | n/a | not checked |
| hover_typ_s3 | 4->14 | 52.0 | 32.00 | 5.69e-05 | 119.2 | 2 | not checked | n/a | n/a | n/a | not checked |
| hover_typ_s3 | 14->18 | 120.0 | 39.75 | 1.23e-04 | 42.9 | 1 | not checked | n/a | n/a | n/a | not checked |
| hover_harsh_s1 | 17->4 | 37.2 | 23.00 | 2.94e-04 | 311.6 | 3 | not checked | 22.25 | 3.78e-04 | 953.4 | not checked |
| hover_harsh_s1 | 4->14 | 52.0 | 70.00 | 1.37e-04 | 821.8 | 2 | not checked | 70.00 | 1.01e-04 | 808.8 | not checked |
| hover_harsh_s1 | 14->18 | 119.2 | 22.75 | 2.95e-04 | 140.8 | 0 | not checked | 23.50 | 2.29e-04 | 46.7 | not checked |
| hover_harsh_s2 | 17->4 | 37.2 | 20.00 | 4.84e-04 | 315.7 | 1 | not checked | 22.25 | 4.28e-04 | 1683.1 | not checked |
| hover_harsh_s2 | 4->14 | 52.0 | 70.00 | 1.36e-04 | 890.8 | 1 | not checked | 70.00 | 1.02e-04 | 523.3 | not checked |
| hover_harsh_s2 | 14->18 | 120.0 | 22.00 | 2.41e-04 | 75.6 | 3 | not checked | 22.50 | 2.40e-04 | 183.9 | not checked |
| hover_harsh_s3 | 17->4 | 37.2 | 20.00 | 2.99e-04 | 150.2 | 0 | not checked | n/a | n/a | n/a | not checked |
| hover_harsh_s3 | 4->14 | 52.0 | 70.00 | 1.38e-04 | 1000.7 | 1 | not checked | n/a | n/a | n/a | not checked |
| hover_harsh_s3 | 14->18 | 120.0 | 22.50 | 2.64e-04 | 145.4 | 1 | not checked | n/a | n/a | n/a | not checked |
| cruise_quiet_s1 | 17->4 | 37.2 | 22.25 | 1.53e-04 | 4062.7 | 0 | not checked | n/a | n/a | n/a | not checked |
| cruise_quiet_s1 | 4->14 | 52.0 | 20.50 | 2.16e-05 | 106.9 | 1 | not checked | n/a | n/a | n/a | not checked |
| cruise_quiet_s1 | 14->18 | 82.3 | 39.75 | 1.00e-04 | 110.7 | 1 | not checked | n/a | n/a | n/a | not checked |
| cruise_quiet_s2 | 17->4 | 37.2 | 22.25 | 1.53e-04 | 8407.3 | 0 | not checked | n/a | n/a | n/a | not checked |
| cruise_quiet_s2 | 4->14 | 52.0 | 21.00 | 1.34e-05 | 90.0 | 3 | not checked | n/a | n/a | n/a | not checked |
| cruise_quiet_s2 | 14->18 | 83.2 | 38.00 | 1.02e-04 | 95.6 | 1 | not checked | n/a | n/a | n/a | not checked |
| cruise_quiet_s3 | 17->4 | 37.2 | 22.25 | 1.49e-04 | 2562.6 | 2 | not checked | n/a | n/a | n/a | not checked |
| cruise_quiet_s3 | 4->14 | 52.0 | 21.25 | 1.46e-05 | 29.2 | 1 | not checked | n/a | n/a | n/a | not checked |
| cruise_quiet_s3 | 14->18 | 82.4 | 38.00 | 1.05e-04 | 92.8 | 0 | not checked | n/a | n/a | n/a | not checked |
| cruise_typ_s1 | 17->4 | 37.2 | 22.25 | 1.59e-04 | 891.8 | 2 | not checked | n/a | n/a | n/a | not checked |
| cruise_typ_s1 | 4->14 | 52.0 | 32.00 | 5.39e-05 | 116.7 | 3 | not checked | n/a | n/a | n/a | not checked |
| cruise_typ_s1 | 14->18 | 82.5 | 87.75 | 1.15e-04 | 30.7 | 3 | not checked | n/a | n/a | n/a | not checked |
| cruise_typ_s2 | 17->4 | 37.2 | 22.25 | 1.77e-04 | 271.4 | 0 | not checked | n/a | n/a | n/a | not checked |
| cruise_typ_s2 | 4->14 | 52.0 | 32.00 | 5.54e-05 | 98.8 | 3 | not checked | n/a | n/a | n/a | not checked |
| cruise_typ_s2 | 14->18 | 82.3 | 38.00 | 1.18e-04 | 52.1 | 1 | not checked | n/a | n/a | n/a | not checked |
| cruise_typ_s3 | 17->4 | 37.2 | 22.25 | 1.87e-04 | 290.8 | 3 | not checked | n/a | n/a | n/a | not checked |
| cruise_typ_s3 | 4->14 | 52.0 | 70.00 | 5.26e-05 | 94.0 | 3 | not checked | n/a | n/a | n/a | not checked |
| cruise_typ_s3 | 14->18 | 82.3 | 87.75 | 1.15e-04 | 30.8 | 0 | not checked | n/a | n/a | n/a | not checked |
| cruise_harsh_s1 | 17->4 | 37.2 | 20.00 | 4.47e-04 | 740.2 | 2 | not checked | 22.25 | 3.93e-04 | 958.1 | not checked |
| cruise_harsh_s1 | 4->14 | 52.0 | 70.00 | 1.41e-04 | 894.3 | 2 | not checked | 20.00 | 2.03e-04 | 453.8 | not checked |
| cruise_harsh_s1 | 14->18 | 83.2 | 22.75 | 2.28e-04 | 178.9 | 0 | not checked | 22.50 | 2.70e-04 | 289.2 | not checked |
| cruise_harsh_s2 | 17->4 | 37.2 | 22.75 | 2.86e-04 | 440.2 | 2 | not checked | 22.25 | 3.88e-04 | 1082.7 | not checked |
| cruise_harsh_s2 | 4->14 | 52.0 | 70.00 | 1.39e-04 | 854.9 | 1 | not checked | 70.00 | 1.01e-04 | 724.7 | not checked |
| cruise_harsh_s2 | 14->18 | 82.3 | 21.50 | 2.89e-04 | 251.1 | 2 | not checked | 23.75 | 2.13e-04 | 72.7 | not checked |
| cruise_harsh_s3 | 17->4 | 37.2 | 23.00 | 2.94e-04 | 305.0 | 3 | not checked | n/a | n/a | n/a | not checked |
| cruise_harsh_s3 | 4->14 | 52.0 | 70.00 | 1.39e-04 | 865.2 | 1 | not checked | n/a | n/a | n/a | not checked |
| cruise_harsh_s3 | 14->18 | 82.4 | 22.00 | 2.71e-04 | 212.2 | 2 | not checked | n/a | n/a | n/a | not checked |

**guard: 0 checked, 0 FAIL** (54 transitions in 18 INDI runs; PID references exist for hover/cruise harsh s1, s2 only).
Max INDI narrow RMS: 4.84e-04 at hover_harsh_s2 17->4 (20.00 Hz); floor 5e-4, upper bound 1e-3. No window reaches the floor, so no transition is checked.
PID values for unchecked transitions are informational (largest-RMS window).
