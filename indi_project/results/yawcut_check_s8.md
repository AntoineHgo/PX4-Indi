# INDI yaw cutoff check (session 8, 2026-11-14)

Firmware 7da2dc5456 (MC_INDI_YAW_CUT, D-yawfilt). gz_x500, seed 1, one flight
each: smoke-level evidence, not a benchmark result. Overlays:
`bench/params/indi_v1.params` (in-loop G1 241/241/7.4) and
`bench/params/indi_v1_yc10.params` (same + MC_INDI_YAW_CUT 10).
Log: `results/yawcut_check_s8.log`; runs under `results/runs/{hover,step_yaw}/`.

| run | motor-rate RMS [1/s] | yaw RMS [deg] | position RMS [m] |
|---|---|---|---|
| hover, pid_default | 0.037 | 0.024 | 0.033 |
| hover, indi_v0 (G1_Y 30, session 7) | 0.300 | | |
| hover, indi_v1 (G1_Y 7.4, no yaw cut) | 1.616 | 0.023 | 0.049 |
| hover, indi_v1 + yaw cut 10 Hz | **0.228** | 0.020 | 0.022 |
| step_yaw x4, pid_default | 0.559 | 13.84 | 0.229 |
| step_yaw x4, indi_v1 | 3.768 | 11.99 | 0.136 |
| step_yaw x4, indi_v1 + yaw cut 10 Hz | 3.691 | 11.98 | 0.283 |

Reading:

- With the identified G1_Y = 7.4, yaw noise reaches the torque with a 4x
  larger gain than in v0, so hover effort rises to 44x PID. The 10 Hz yaw
  low-pass on the synchronised pair cuts it 7x, to 6x PID. This confirms
  the D-yawfilt diagnosis. The remaining excess is not explained yet:
  probably roll/pitch a_f noise through 1/G1 (to check with check_sync.py).
- step_yaw: INDI tracks yaw slightly better (12.0 vs 13.8 deg RMS) at 6.7x
  the motor-rate effort; the yaw cutoff does not change that effort, so it
  comes from the step response itself (K_Y, saturation), not from noise.
  INDI tuning round 1 (effort-penalised cost, same as PID) decides K_Y.
- First attempt of the indi_v1 runs failed (rc=1): two parallel
  `run_batch.sh` calls without `NAME_TAG` gave the same container name.
  Tooling note, not a flight failure; re-flown with NAME_TAG.
