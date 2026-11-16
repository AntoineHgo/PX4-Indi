# Second-key check, s29 (independent ULog computation)

Primary values: `python3 indi_flight/bench/metrics.py --run-json <run>/run.json --out indi_flight/results/second_key_s29/primary_<scen>_<rep>.json <run>/flight.ulg` for each run (scratch output, existing metrics.json untouched).
Second key: `python3 indi_flight/bench/second_key_s29.py` (reads the primary scratch JSON for window only, then computes independently).

Tolerance (G1.3): max(1 % of primary, absolute). Absolute parts: attitude 0.1 deg; effort 0.1 % of FS with FS = 1.0 (normalized motor control, assumed); rates have no absolute unit in G1.3 so 1 % relative only.

Setpoint/attitude conventions: rate setpoint zero-order held onto truth times; attitude setpoint zero-order hold; quaternions w-first (PX4 convention).

## Windows (ULog time, us)

| run | window start us | window end us |
|---|---|---|
| hover/r1 | 55013750 | 85025750 |
| hover/r2 | 55020000 | 85020000 |
| step_roll/r1 | 55017500 | 69017500 |
| step_roll/r3 | 55011250 | 69011249 |
| traj_lemniscate/r1 | 55020000 | 78237226 |

## Comparison

| run | metric | primary | key | rel diff | verdict |
|---|---|---|---|---|---|
| hover/r1 | rate roll (rad/s) | 0.000942441 | 0.000942441 | +0.000 % | AGREE |
| hover/r1 | rate pitch (rad/s) | 0.00070581 | 0.00070581 | +0.000 % | AGREE |
| hover/r1 | rate yaw (rad/s) | 0.000177368 | 0.000177368 | +0.000 % | AGREE |
| hover/r1 | attitude rot-angle RMS (deg) | 0.556262 | 0.655448 | +17.831 % | AGREE |
| hover/r1 | motor_rate_rms_per_s (mean of 4) | 0.00348441 | 0.00348346 | -0.027 % | AGREE |
| hover/r2 | rate roll (rad/s) | 0.000876073 | 0.000876073 | +0.000 % | AGREE |
| hover/r2 | rate pitch (rad/s) | 0.000889732 | 0.000889732 | +0.000 % | AGREE |
| hover/r2 | rate yaw (rad/s) | 0.000177169 | 0.000177169 | +0.000 % | AGREE |
| hover/r2 | attitude rot-angle RMS (deg) | 0.566125 | 0.663903 | +17.271 % | AGREE |
| hover/r2 | motor_rate_rms_per_s (mean of 4) | 0.00377285 | 0.00377228 | -0.015 % | AGREE |
| step_roll/r1 | rate roll (rad/s) | 0.130413 | 0.130413 | +0.000 % | AGREE |
| step_roll/r1 | rate pitch (rad/s) | 0.00186698 | 0.00186698 | +0.000 % | AGREE |
| step_roll/r1 | rate yaw (rad/s) | 0.00046954 | 0.00046954 | +0.000 % | AGREE |
| step_roll/r1 | attitude rot-angle RMS (deg) | 2.61348 | 2.63111 | +0.674 % | AGREE |
| step_roll/r1 | motor_rate_rms_per_s (mean of 4) | 0.101055 | 0.101064 | +0.009 % | AGREE |
| step_roll/r3 | rate roll (rad/s) | 0.13377 | 0.13377 | +0.000 % | AGREE |
| step_roll/r3 | rate pitch (rad/s) | 0.00162261 | 0.00162261 | +0.000 % | AGREE |
| step_roll/r3 | rate yaw (rad/s) | 0.000484415 | 0.000484415 | +0.000 % | AGREE |
| step_roll/r3 | attitude rot-angle RMS (deg) | 2.6282 | 2.64996 | +0.828 % | AGREE |
| step_roll/r3 | motor_rate_rms_per_s (mean of 4) | 0.10449 | 0.1045 | +0.009 % | AGREE |
| traj_lemniscate/r1 | rate roll (rad/s) | 0.023196 | 0.0231968 | +0.004 % | AGREE |
| traj_lemniscate/r1 | rate pitch (rad/s) | 0.0372779 | 0.03728 | +0.006 % | AGREE |
| traj_lemniscate/r1 | rate yaw (rad/s) | 0.0982901 | 0.0982903 | +0.000 % | AGREE |
| traj_lemniscate/r1 | attitude rot-angle RMS (deg) | 5.41098 | 5.42159 | +0.196 % | AGREE |
| traj_lemniscate/r1 | motor_rate_rms_per_s (mean of 4) | 0.0428402 | 0.0428424 | +0.005 % | AGREE |

