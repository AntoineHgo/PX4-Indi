# Stage-2 sim: rotor-speed IMU vibration check (session 28, 2026-11-14)

hover, PID defaults, seed 1, speed 1, `--sim v2 --erpm-drop 0.01 --imu-rate 1000`; vibration from
`SIM_GZ_VIB_ACC/GYR` (6678cbf3dc), amplitudes per rotor at SIM_GZ_VIB_RPM 7000. Numbers: `bench/vib_check.py`
over the metric window (raw lines in `s2_vib_check/vib_check_s28.jsonl`). Accel p-p = 1st-99th percentile of
`sensor_combined` (250 Hz integrated output, the signal PX4's log analysis looks at).

| vib acc / gyr | accel x/y p-p [m/s^2] | accel vib metric | gyro vib metric | gyro x peak [Hz] | att rms [deg] | pos rms [m] |
|---|---|---|---|---|---|---|
| off | 0.016 / 0.016 | 0.12 | 0.002 | 6.9 | 0.093 | 0.023 |
| 0.25 / 0.02 | 0.121 / 0.122 | 0.17 | 0.006 | 122 | 0.092 | 0.021 |
| 2.0 / 0.1 | 2.12 / 2.12 | 1.54 | 0.072 | 122 | 0.099 | 0.022 |

- Measured hover rotor speed 6890-6917 rpm (1P 115 Hz, blade pass 230 Hz); SIM_GZ_VIB_RPM 7000 is the hover reference.
- The gyro spectrum peak moves to the rotor frequency band (122 Hz in the 250 Hz `sensor_combined`, near Nyquist; the
  1 kHz control path sees it unaliased). PID hover is unaffected at both levels (attitude/position RMS within noise).
- Reference: PX4 `docs/en/log/flight_log_analysis.md:16`, "strong vibration" = accel peak-to-peak above 2-3 m/s^2.
  2.0/0.1 sits at that threshold. No quantitative source was found for gyro vibration; the gyro amplitude is
  scaled with the accel one (an assumption, stated as such).
- Not done: check with INDI (none flies on v2 before the PID re-baseline), and a 1.0/0.05 confirmation flight.
