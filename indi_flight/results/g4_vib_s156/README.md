# S156 vibration hook pre-test (A-49 closing test, D-VIB-HOOK)

Probe, one flight. Firmware d819543d9b + uncommitted D-VIB-HOOK (committed next, same session), SITL rebuilt.
Command (repo root): `timeout 900 indi_project/docker/run.sh -n s156vib -t 900 -- python3 indi_flight/bench/run_scenario.py
--scenario hover --controller indi --model quad5in --seed 1 --speed 4 --sim v2 --params indi_flight/results/g5_g57_s153/params.params
--gps-dly 110 --gnss-delay 110 --vib-acc 10 --vib-gyr 0 --out indi_flight/results/g4_vib_s156/hover_typ_s1`
(runner now sets SIM_GZ_VIB_RPM 9540, SIM_GZ_VIB_NB 3 for quad5in; sensor_accel logged at full rate).
Check: `python3 indi_flight/bench/vib_line_check.py <log> --t0 58 --t1 72 --nb 3` (self-test `--selftest` OK), output
`vib_line_check_s1.txt`. Window ends at 72 s: the flight lands after ~74 s.

| line | target (typical, at 9540 rpm) | measured | error |
|---|---|---|---|
| 1P x, y (158.8 Hz) | 10.0 m/s^2 | 9.70 m/s^2 | -3 % |
| blade-pass z (477 Hz, aliased 323.2 Hz) | 5.0 m/s^2 | 4.80 m/s^2 | -4 % |
| sqrt(2) x std of x per 2 s chunk, 56-72 s | 10.0 + noise | 9.96-10.00 | <1 % |

Mean rotor speed 9512 rpm (std 128). The band estimator reads ~3 % low from the line width (speed wander); the
envelope agrees within 1 %. A-49 closing test (within 10 %): PASS on one key; key2 in design/vib_hook_key2.md.
Note: the params file used carries MC_INDI_POS_TB 1.0 (S153); the G5 re-fly must use the freeze params (TB 0.3).
