# S64: G2-STEP first formal test (2026-11-17)

Provenance (G1.7): firmware built at HEAD 360c9ae453 (`../stage3_s64/head.txt`: no tracked change, only untracked
results; `../stage3_s64/build.log` rc 0). Command: `../stage3_s64/fly_effort.sh` (copy `fly.sh.ref`), same flight
command as `stage3_s62/fly_steps.sh`: quad5in, sim v2 (eRPM), 800 Hz, speed 4, seeds 1-3, `indi.params` (= S62:
firmware INDI defaults + derived G1/G2_Y + CA_R_W_MAX 2700 + SENS_BAR_AUTOCAL 0). 12 flights, all rc 0 (`done.txt`).

Primary: `python3 bench/g2_step_metrics.py results/g2_step_s64/g2_step_primary.json results/g2_step_s64/steps_seed{1,2,3}/step_{roll,pitch,yaw}_indi`
Second key: `bench/t127_step_metrics_key.py` per flight -> `key_all.md` (est_g2 / gt_g2 rows).

| seed | axis | est OS % | est settle ms | truth OS % | rise ms | est-truth end deg | pass |
|---|---|---|---|---|---|---|---|
| 1 | roll | 0.66 | 366 | 0.39 | 206 | 0.23 | yes |
| 1 | pitch | 0.96 | 360 | 0.71 | 209 | 0.24 | yes |
| 1 | yaw | 0.20 | 923 | 0.00 | 552 | 0.78 | yes |
| 2 | roll | 1.21 | 365 | 1.00 | 210 | 0.21 | yes |
| 2 | pitch | 0.64 | 358 | 0.60 | 211 | 0.22 | yes |
| 2 | yaw | 0.37 | 923 | 0.00 | 550 | 0.94 | yes |
| 3 | roll | 1.29 | 366 | 1.29 | 208 | 0.22 | yes |
| 3 | pitch | 0.84 | 341 | 0.71 | 203 | 0.24 | yes |
| 3 | yaw | 0.18 | 913 | 0.00 | 546 | 0.82 | yes |

Limits: roll/pitch OS <= 5 %, settle <= 450 ms; yaw OS <= 5 %, settle <= 1350 ms; truth OS <= 5 %. **9/9 PASS at 800 Hz.**
Second key AGREES on every pass metric (est OS, est settle, truth OS identical to the rounding); rise differs by up to
3 ms (seed 2 pitch 213.8 vs 210.8; interpolation, not a pass metric). Truth settle (reported only) is long on seed 2/3
pitch (2.2 s) and NaN on seed 2 yaw: the truth sits outside the 2 % band of the setpoint by the stock-EKF est-truth
offset (A-28, closed S63), as written in GATES.md.
Torque-step rejection (also checked, not pass; `results/indi_vs_pid/plot_compare.py`, `steps_seedN/metrics.md`): peak
angle roll 11.3-11.8 deg, pitch 10.6-11.0, yaw 4.3-4.4; S61 INDI 12.9 / 12.4 / 4.6: no regression.
Not yet done for G2-STEP: the 400 Hz reported run.
