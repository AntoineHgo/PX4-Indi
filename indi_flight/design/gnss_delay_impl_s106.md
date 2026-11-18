# Hook B: SIM_GZ_GPS_DLY implementation (S106)

- GNSS path flown: gz navsat (quad5in_base/model.sdf navsat_sensor, 30 Hz) -> GZBridge::navSatCallback -> sensor_gnss. sensor_gps_sim not used.
- Param SIM_GZ_GPS_DLY int32 ms 0-250 default 0 reboot_required (module.yaml). 0 = original publish path, never through the ring.
- Ring: 32 x sensor_gnss_s per instance (250 ms at 30 Hz = 8, 50 Hz = 14), mutex _gnss_delay_mutex (not nested with _node_mutex).
  Release in callback and in Run() 10 ms loop (delivery quantised to 10 ms). Overflow: oldest released early, counted, one PX4_WARN.
- timestamp_sample unchanged; timestamp = release time. process_gnss + _failure_config.update() applied at release.
- EKF finding: EKF2.cpp:2653 gnssSample.time_us = vehicle_gnss.timestamp_sample (not timestamp); EKF2.cpp:995 SENS_GNSS0_DELAY only sizes the buffer.
  Matched compensation = SENS_GNSS0_DELAY = L (EKF looks up the sample at imu_time - delay). Note: with a delivered-late sample, the EKF
  sample is stamped t, which it sees at t+L; with delay param L it compares against delayed state at t. Param does not shift stamps.
- run_scenario.py: --gps-dly (0..250), env PX4_PARAM_SIM_GZ_GPS_DLY, run.json gps_dly_ms.
- Build: `make px4_sitl_default` in docker exit 0, 0 warnings; astyle unchanged on GZBridge.cpp/.hpp.
- Flight: results/gnss_delay_pretest_s106/d200 (hover_long, indi_m3a, seed 1, --gps-dly 200), exit_status ok, run.json gps_dly_ms 200.
  px4.log: init "requested 200000 us (delay line active)", first release "applied 200000 us", no overflow line.
  ulog sensor_gnss (age.py): logged at ~1.01 Hz (n=110), age = timestamp - timestamp_sample median/min/max 200000/200000/200000 us, 0 negative.
- UNVERIFIED: ages exactly 200000 (hrt tick granularity equals release time; real jitter not exposed at 1 Hz log); EKF response/matched-mismatched
  behaviour not evaluated; failure injection (stuck/dropout) at release not exercised; overflow path not exercised; multi-instance (EN_GPS=2) not run;
  gz GNSS logged only 1 Hz so rate of 30 Hz is from the SDF, not measured.

## S106 correction (orchestrator, after K106)
Releasing with the true `timestamp_sample` made `SENS_GNSS0_DELAY` inert (VehicleGPSPosition keeps a driver
sample time below `timestamp`). The release now stamps `timestamp_sample = timestamp`; true age goes to
`age_min_us/age_max_us` (print_status `age0`). Evidence: `results/gnss_delay_key_s106/README.md`.
