# First INDI flights (session 6, 2026-11-13)

Config: `bench/params/indi_v0.txt` (MC_RATE_CTL_TYPE=1, all MC_INDI_* at
defaults: G1 R/P/Y 320/210/30, K 20/20/10 rad/s, ACT_TC 0.02 s, delay 0).
gz_x500, seed 1, speed 1. Compared against the existing pid_default seed 1
runs. ONE seed each, untuned INDI: smoke check only, not a result.

Verified in the ULog: MC_RATE_CTL_TYPE=1, 16441 indi_rate_status samples,
fault never set.

| scenario | metric | INDI v0 | PID default |
|---|---|---|---|
| hover | rate rms roll/pitch/yaw (rad/s) | 0.0011/0.0011/0.0007 | 0.0010/0.0010/0.0011 |
| hover | attitude rms (deg) | 0.116 | 0.095 |
| hover | position rms 3D (m) | 0.024 | 0.033 |
| step_roll | roll rate rms (rad/s) | 0.108 | 0.084 |
| step_roll | roll attitude rms (deg) | 3.55 | 3.31 |
| step_roll | delay to 10 % (s, mean of 4) | 0.129 | 0.107 |
| step_roll | rise 10-90 % (s, mean) | 0.431 | 0.414 |
| step_roll | off-axis pitch/yaw rate rms (rad/s) | 0.0011/0.0021 | 0.0036/0.0044 |

Reading: stable and safe with model-derived defaults; on the roll step it is
slower than the default PID (bandwidth K=20 rad/s not tuned) but
decouples the off-axes better. Expected next: tune K and check G1
(roll G1 is the poorly fitted one, R^2 0.63).
