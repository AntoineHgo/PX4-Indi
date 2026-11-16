# Second-key check, s29 (independent ULog computation)

Primary values: `python3 indi_flight/bench/metrics.py --run-json <run>/run.json --out indi_flight/results/second_key_s29/primary_<scen>_<rep>.json <run>/flight.ulg` for each run (scratch output, existing metrics.json untouched).
Second key: `python3 indi_flight/bench/second_key_s29.py` (reads the primary scratch JSON for window only, then computes independently).

Tolerance (G1.3): max(1 % of primary, absolute). Absolute parts: attitude 0.1 deg; effort 0.1 % of FS with FS = 1.0 (normalized motor control, assumed); rates have no absolute unit in G1.3 so 1 % relative only.

Setpoint/attitude conventions: rate setpoint linearly interpolated onto truth times; attitude setpoint zero-order hold; quaternions w-first (PX4 convention).

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
| hover/r1 | rate roll (rad/s) | 0.000942441 | 0.000967943 | +2.706 % | DISAGREE |
| hover/r1 | rate pitch (rad/s) | 0.00070581 | 0.000722954 | +2.429 % | DISAGREE |
| hover/r1 | rate yaw (rad/s) | 0.000177368 | 0.000179113 | +0.984 % | AGREE |
| hover/r1 | attitude rot-angle RMS (deg) | 0.556262 | 0.655448 | +17.831 % | AGREE |
| hover/r1 | motor_rate_rms_per_s (mean of 4) | 0.00348441 | 0.00348346 | -0.027 % | AGREE |
| hover/r2 | rate roll (rad/s) | 0.000876073 | 0.000901314 | +2.881 % | DISAGREE |
| hover/r2 | rate pitch (rad/s) | 0.000889732 | 0.000914975 | +2.837 % | DISAGREE |
| hover/r2 | rate yaw (rad/s) | 0.000177169 | 0.000178714 | +0.872 % | AGREE |
| hover/r2 | attitude rot-angle RMS (deg) | 0.566125 | 0.663903 | +17.271 % | AGREE |
| hover/r2 | motor_rate_rms_per_s (mean of 4) | 0.00377285 | 0.00377228 | -0.015 % | AGREE |
| step_roll/r1 | rate roll (rad/s) | 0.130413 | 0.133885 | +2.662 % | DISAGREE |
| step_roll/r1 | rate pitch (rad/s) | 0.00186698 | 0.0018734 | +0.344 % | AGREE |
| step_roll/r1 | rate yaw (rad/s) | 0.00046954 | 0.000476832 | +1.553 % | DISAGREE |
| step_roll/r1 | attitude rot-angle RMS (deg) | 2.61348 | 2.63111 | +0.674 % | AGREE |
| step_roll/r1 | motor_rate_rms_per_s (mean of 4) | 0.101055 | 0.101064 | +0.009 % | AGREE |
| step_roll/r3 | rate roll (rad/s) | 0.13377 | 0.137501 | +2.789 % | DISAGREE |
| step_roll/r3 | rate pitch (rad/s) | 0.00162261 | 0.00162446 | +0.114 % | AGREE |
| step_roll/r3 | rate yaw (rad/s) | 0.000484415 | 0.000492177 | +1.602 % | DISAGREE |
| step_roll/r3 | attitude rot-angle RMS (deg) | 2.6282 | 2.64996 | +0.828 % | AGREE |
| step_roll/r3 | motor_rate_rms_per_s (mean of 4) | 0.10449 | 0.1045 | +0.009 % | AGREE |
| traj_lemniscate/r1 | rate roll (rad/s) | 0.023196 | 0.0230902 | -0.456 % | AGREE |
| traj_lemniscate/r1 | rate pitch (rad/s) | 0.0372779 | 0.0370654 | -0.570 % | AGREE |
| traj_lemniscate/r1 | rate yaw (rad/s) | 0.0982901 | 0.0983752 | +0.087 % | AGREE |
| traj_lemniscate/r1 | attitude rot-angle RMS (deg) | 5.41098 | 5.42159 | +0.196 % | AGREE |
| traj_lemniscate/r1 | motor_rate_rms_per_s (mean of 4) | 0.0428402 | 0.0428424 | +0.005 % | AGREE |

## Variants and diagnosis (s29)

Run inline during the check (not saved as script options): the rate setpoint
taken zero-order hold (latest `vehicle_rates_setpoint` sample at or before each
truth sample, `np.searchsorted(ts, tt, side='right') - 1`) instead of linear
interpolation. Second-key rate RMS (ZOH) vs primary:

| run | roll (rad/s) | pitch (rad/s) | yaw (rad/s) |
|---|---|---|---|
| hover/r1 | 0.0009424407 vs 0.0009424407 (0.000 %) | 0.0007058099 vs 0.0007058099 (0.000 %) | 0.0001773681 vs 0.0001773681 (0.000 %) |
| hover/r2 | 0.0008760734 vs 0.0008760734 (0.000 %) | 0.0008897316 vs 0.0008897316 (0.000 %) | 0.0001771686 vs 0.0001771686 (0.000 %) |
| step_roll/r1 | 0.1304133 vs 0.1304133 (0.000 %) | 0.001866979 vs 0.001866979 (0.000 %) | 0.0004695404 vs 0.0004695404 (0.000 %) |
| step_roll/r3 | 0.1337704 vs 0.1337704 (0.000 %) | 0.001622605 vs 0.001622605 (0.000 %) | 0.0004844149 vs 0.0004844149 (0.000 %) |
| traj_lemniscate/r1 | 0.0231968 vs 0.02319597 (+0.004 %) | 0.03728003 vs 0.03727786 (+0.006 %) | 0.09829028 vs 0.09829013 (+0.000 %) |

Attitude, primary total vs its own per-axis values (deg):
- hover/r1: primary total 0.556; per-axis roll/pitch/yaw 0.0454/0.0415/0.652 (second key per-axis agrees to 0.001 deg); sqrt-sum of the primary per-axis values is about 0.655, which matches the second-key total (0.655), not the primary total.
- hover/r2: primary total 0.566; per-axis 0.0417/0.0381/0.661; sqrt-sum about 0.663, second key 0.664.
- step_roll/r1: primary total 2.6135; per-axis 2.6056/0.0352/0.3634; sqrt-sum about 2.631, second key ZOH 2.631.

## Causes of DISAGREE and borderline rows

- Rate tracking, 8 DISAGREE rows (hover roll/pitch, step_roll roll/yaw, both runs): interpolation choice. The spec asked for linear interpolation of the setpoint; the primary (and the ZOH variant above) uses the latest setpoint at or before each truth sample. Same window and same fields. With ZOH, all rate rows agree (max 0.006 %). Traj rate rows agree with linear too (<0.6 %).
- Attitude, hover/r1 and hover/r2: marked AGREE only by the 0.1 deg absolute floor (absolute diff 0.099 and 0.098 deg, relative 17.8 % and 17.3 %). Not a real agreement. Cause not identified within budget: the primary total is about 15 % below the sqrt-sum of its own per-axis values, so the suspect is the primary's total-angle aggregation, not the window or the setpoint interpolation. Needs review of the primary code (not read here by constraint).
- Attitude, step_roll and traj: AGREE within 0.7 % and 0.2 %. Interpolation matters for attitude too (step_roll/r1: ZOH 2.631, nearest 2.747, quaternion lerp 2.704), ZOH kept as specified.
- Effort: all 5 AGREE, max |rel| 0.03 % (hover/r1 -0.027 %).
