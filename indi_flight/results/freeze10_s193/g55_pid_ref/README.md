# G5.5 o2_circle_z stock PID reference (freeze-10, seeds 1-3)

Purpose: tell whether the INDI gate fail (o2_circle_z s1, H 0.5027 m) is INDI-specific.

Command (per seed, serial, same plant as the INDI flights in `freeze10_s193/queue.sh` step 2):
`indi_project/docker/run.sh -n s193pid_o2_circle_z_s$sd -t 900 -- python3 indi_flight/bench/run_scenario.py --controller pid_default --model quad5in --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0 --seed $sd --scenario o2_circle_z --out .../g55_pid_ref/o2_circle_z_s$sd`
No `--params` file (same as the S139 precedent `g5_g55_s139/pid_ref`). Matched GNSS 110 ms kept.

PID verified: `run.json` has controller `pid_default`, params_file null, no MC_INDI_EN/MC_RATE_CTL_TYPE/MC_INDI_POS_EN
applied, no boot_params. The ULog has `rate_ctrl_status` and `vehicle_rates_setpoint` (stock rate loop) and no
`indi_*` topics (INDI flights have `indi_pos_status`, `indi_rate_status`, `indi_rate_feedforward`). Only
`MC_INDI_ID_OK 1` is in the runner's defaults, inert with MC_INDI_EN 0.

Scoring: `bench/g55_check.py` (key 1) and `bench/g55_g57_key2.py g55` (key 2). Checker marks all three INVALID only for
`indi_pos_status not logged` (expected for PID); H and V RMS are reported below.

| seed | PID key1 H / V [m] | PID key2 H / V [m] | INDI key1 H / V [m] | INDI key2 H / V [m] |
|---|---|---|---|---|
| 1 | 1.157 / 0.089 | 1.158 / 0.089 | 0.503 / 0.023 (FAIL) | 0.503 / 0.023 (FAIL) |
| 2 | 1.144 / 0.042 | 1.144 / 0.042 | 0.491 / 0.082 | 0.491 / 0.082 |
| 3 | 1.146 / 0.053 | 1.147 / 0.053 | 0.496 / 0.033 | 0.496 / 0.033 |

No LOC on any PID seed (key 1 and key 2). PID H RMS is about 2.3x the INDI value and exceeds 0.5 m on all seeds.
