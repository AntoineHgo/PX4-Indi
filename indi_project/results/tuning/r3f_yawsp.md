# r3 c13 re-scored with D-yawsp firmware (session 13)

Command: see header of `r3f_yawsp.log` (c13 centre `bench/params/indi_c13_r3.json`, 1 candidate, seeds 1-3, firmware
99634a6b71). 15 flights, 0 failures.

| | J | hover | step_roll | step_pitch | step_yaw | rate_step_roll |
|---|---|---|---|---|---|---|
| PID defaults (r2) | 0.958-0.964 | | | | | |
| c13, D-yawnu firmware (r3) | 1.055 | 0.740 | 0.858 | 0.951 | 0.876 | 1.035 |
| c13, D-yawsp firmware | 1.058 | 1.306 | 0.877 | 0.924 | 1.056 | 1.021 |

Motor-rate effort ratio to PID (min-max over seeds): hover 1.01-1.02, step_roll 1.12-1.36, step_pitch 0.66-0.73,
**step_yaw 1.42-1.42 (was 4.66-5.89)**, rate_step_roll 0.67.

step_yaw seed 1, `bench/yaw_step_effort.py`: motor-rate RMS around each step 1.13 (D-yawnu 4.70, PID 0.79), peak yaw
torque 0.45 (0.78, PID 0.33). The fix does what it was meant to do: the setpoint step no longer passes as a step
into the torque. Price: yaw tracking ratio 0.876 -> 1.056 (the lag PID also pays with its 2 Hz torque filter).
Roll/pitch are unchanged within noise, as expected (yaw-only change).

## Hover term is noise-dominated

J did not move because hover went 0.740 -> 1.306, from one run (seed 1: 0.067 m, the other seeds 0.017 / 0.026).
Split over all hover runs:

| set | runs | horizontal RMS median / max (m) | vertical RMS median / max (m) |
|---|---|---|---|
| PID defaults | 3 | 0.0188 / 0.0254 | 0.0093 / 0.0276 |
| PID r2 candidates | 48 | 0.0204 / 0.0253 | 0.0075 / 0.0699 |
| INDI r3 candidates | 48 | 0.0194 / 0.0242 | 0.0072 / 0.0410 |
| INDI c13 D-yawsp | 3 | 0.0180 / 0.0234 | 0.0122 / 0.0646 |

Horizontal hover error, the part attitude control acts on, is tight and equal for both families. The hover score is
driven by sporadic vertical excursions (up to 0.3 m peak in the outlier run, inside the 30 s window) that occur
for PID as well. Altitude is controlled by the same position loop and thrust path for both controllers, so these
excursions are not attributed to INDI; their cause is not identified yet (open). With 3 seeds, one such run moves
the hover ratio by ~0.5 and J by ~0.1. The frozen cost stays as is (no after-the-fact change), but J differences
below ~0.1 between candidates are not meaningful, and the final benchmark must use more seeds and report the
horizontal/vertical split.

Next: D-r4 (yaw-only sweep around c13 under D-yawsp) to recover yaw tracking at acceptable effort.
