# Delay-hook pre-test s102 (SIM_GZ_DLY_ACT / SIM_GZ_DLY_IMU)

## Commands
- `fly.sh` (repo root): hover_long, indi_m3a, seed 1, speed 4, quad5in, 800 Hz, sim v2; d0 = `--dly-act 0 --dly-imu 0`, d5 = `--dly-act 5 --dly-imu 5`. Both exit=0, serial, in docker.
- Gate (docker): `pretest_gate.py d{0,5}/flight.ulg d{0,5}/gate.md --delay 4 --length 15`
- Checks (docker): `check_delay.py d0/flight.ulg d5/flight.ulg` -> `check.out`; lag diagnostic `diag_lag.py` -> `diag_lag.out`.
- hover_long exists in `indi_flight/bench/scenarios.py` (60 s hold); no substitution.

## Flight status
- Both flew: run.json `exit_status` ok, `error` null, `metrics_status` ok.
- run.json has `dly_act_ms` / `dly_imu_ms`: d0 0/0, d5 5/5.
- Gate: PASS for d0 and d5.
- Logs: `d{0,5}.stdout.log` are empty (console not captured there). PX4 console is in `d{0,5}/px4.log`. `grep SIM_GZ_DLY` hits there; `grep -i overflow` over px4.log and gz.log: no hits.
- d0 px4.log: "SIM_GZ_DLY_IMU/ACT requested 0 us (bypassed)".
- d5 px4.log: "SIM_GZ_DLY_IMU IMU 0 applied 5000 us for requested 5000 us (first release)"; "SIM_GZ_DLY_ACT applied 135000 us for requested 5000 us (first release)"; "SIM_GZ_DLY_ACT: output calls irregular, due commands skipped (counted, latest wins)".

## Measurements
- Logged rates: sensor_gyro, actuator_motors, esc_status all 800 Hz nominal (median dt).
- (a) IMU age, sensor_gyro instance 0 (us):
  - d0: median 0, min 0, max 0, n 89058. Negative control: not ~5000, PASS.
  - d5: median 5000, min 5000, max 5000, n 88352. PASS (expected 5000 +-1250).
- (b) Actuator lag: **UNVERIFIED (method invalid)**.
  - esc_status `esc_rpm` changes only ~12 times/s in both logs, despite 800 Hz logging. It is a held/slow telemetry value, so a 1.25 ms grid cannot resolve a 5 ms lag.
  - Command excitation in hover is tiny (control[0] std 0.0008).
  - Script output: d0 per-motor 31.25 ms, d5 median 29.38 ms, d5-d0 = -1.88 ms. The script labelled this FAIL, but the diagnostic shows the correlation curve is flat and the value is not physical. Treat as no result, not as a hook failure.

## Unexpected
- d5 ACT log "applied 135000 us for requested 5000 us (first release)" and "output calls irregular, due commands skipped". The actuator delay may not be 5 ms at start-up or with irregular ESC output calls. Not investigated.
- esc_status is not usable for lag at this rate (see above).

## Result
- IMU delay hook: PASS (0 and 5000 us exact in the log).
- Actuator delay hook: applied and logged, but its effect is UNVERIFIED. Needs a higher-excitation maneuver and a faster rotor-speed source (e.g. actuator-side or sim truth) before a 5 ms claim.
