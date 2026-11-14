# Stage-2 held-out sim hooks: smoke check (session 36, harness check only)

PID defaults + `v2_fac.params`, v2 sim (`--sim v2 --imu-rate 1000 --erpm-drop 0.01 --vib-acc 1.0 --vib-gyr 0.05`),
build/px4_sitl_omega2 with 48d82eacda, seed 1, speed 4. Script `results/s2_vhooks_check/run.sh`. Not a benchmark
result: no INDI flight, no metric is compared.

| scenario | flew | plant change seen in the log |
|---|---|---|
| v2_drop_att (V4) | yes, no error | esc_errorcount increments per logged esc_status sample (5 ms): ~1.0 on all motors before/after (20 % of 5 frames at 1 kHz), motor 0 4.84 during the 3 s loss window (every frame fails), others 1.0 |
| v2_sag_att (V6) | yes, no error | SIM_GZ_THR_SC staircase 1.0 -> 0.85 in 0.5 s steps (run.json); mean motor command 0.582 -> 0.687 (x1.18) while mean rotor speed stays 7267 -> 7331 rpm: same thrust needs a larger command |
| v2_lat_att (V3) | yes, no error | NOT verified: esc_status is logged at 5 ms, coarser than the 1 ms frame. The frame is one gz motor-speed message; that it is 1 ms at 1000 Hz physics is assumed, check with a full-rate log before quoting a latency in ms |
