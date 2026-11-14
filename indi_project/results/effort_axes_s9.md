# Per-axis effort breakdown in hover (session 9)

Script: `bench/effort_axes.py` (window t0+15 s to t0+45 s of each log),
run in Docker on seed-1 hover logs.

| run | tq roll std / dRMS | tq pitch std / dRMS | tq yaw std / dRMS | motor-rate RMS (1/s) |
|---|---|---|---|---|
| pid_default | 0.0002 / 0.0001 | 0.0002 / 0.0001 | 0.0003 / 0.0000 | 0.054 |
| indi_v1 (no yaw cut) | 0.0002 / 0.0002 | 0.0002 / 0.0002 | 0.0077 / 0.0066 | 1.618 |
| indi_v1_yc10 (yaw cut 10 Hz) | 0.0002 / 0.0002 | 0.0002 / 0.0002 | 0.0027 / 0.0010 | 0.230 |

(tq = normalised `vehicle_torque_setpoint`; dRMS = RMS of the per-sample
change.) Angular-rate std is the same for all three runs (roll/pitch
~0.005 rad/s, yaw ~0.0013 rad/s): the extra INDI effort buys no rate
stability in hover.

Reading: the remaining INDI hover effort is yaw. Its torque std is 9x
PID's; roll/pitch are at ~2x PID's per-sample activity. PID filters its
yaw torque at 2 Hz by default (`MC_YAW_TQ_CUTOFF`), INDI at 10 Hz here.
With G1_yaw = 7.4 (vs 241 roll/pitch) every rad/s^2 of residual yaw
acceleration noise becomes 33x more torque than on roll/pitch. This
motivates round 2's lower yaw-cutoff box (D-r2).
