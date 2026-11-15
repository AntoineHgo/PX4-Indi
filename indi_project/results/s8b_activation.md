# INDI POS first activation (stage-8 task B, session 51, 2026-11-15)

Hover seed 1, v2 sim (imu 1000 Hz, eRPM drop 0.01, vibration 1.0 m/s^2 / 0.05 rad/s), pid_tuned inner loops,
MC_INDIP_EN 1, default MC_INDIP_* (LPF 10 Hz, G_T 16.63, K_CMD 1, DLY 1, FF 1), MC_INDI_W_MAX 1000. Diagnostic only.
Scripts `bench/s8b_activation.sh`, `bench/s8b_activation_check.py`; output `s8b_activation/hover_seed1/check.txt`.

- Try 1: commander accepted registration (mode_id 23) and the arming reply; the offboard switch gave nav_state 23
  (EXTERNAL1) and INDI POS held the hover 30 s, but the runner waited for main mode 6 and the status topic was not
  logged. Fixed in two commits (status advertised at init; runner accepts AUTO/EXTERNALn when MC_INDIP_EN).
- Try 2: run completed (engage, hover window, land). indi_pos_status 125 Hz, 0 hold cycles, 0 failures,
  mean_u valid 100 % (median 0.595), thrust median 0.590 (0.574-0.624), jerk from the a_ref difference (MAVLink
  sends no jerk), omega_ff 0 at hover. Engaged custom mode recorded in run.json `offboard_custom_mode`.
- **Problem: attitude rms 5.47 deg (pid_tuned hover 0.06-0.16 deg).** Horizontal a_f std 1.05/1.13 m/s^2, t_c std
  0.98/1.05 m/s^2 (~6 deg of tilt) while a_c std is only 0.44: the measured acceleration noise passes straight into
  the thrust-vector command (t_c = t_f + a_c - a_f). Hypothesis to test first: the module takes the LATEST
  sensor_combined accelerometer sample once per 125 Hz cycle, so rotor-frequency vibration aliases below the 10 Hz
  low-pass. Candidate fixes (choose and record in DECISIONS before tuning): average all accelerometer samples
  between cycles, or use vehicle_acceleration; check also with --vib-acc 0 to separate vibration from loop dynamics.
  Caveat: the attitude metric compares against vehicle_attitude_setpoint, which INDI POS does not publish.
