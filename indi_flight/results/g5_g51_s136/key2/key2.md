# G5.1 independent second key (key2), S136

Script: `key2/g51_key2.py` (run as `python3 g51_key2.py <run_dir> acro|stab`).
Sources: `flight.ulg` (pyulog) and `sticks.csv`; truth topics `vehicle_angular_velocity_groundtruth`, `vehicle_attitude_groundtruth`.

## wdoff_acro_s1 (acro)

Commanded rate = stick/1000 x 100 deg/s (roll +y, pitch -x, yaw +r). RMS of (commanded - truth) over [edge + 0.1 s, next edge], zero plateau capped at 1.0 s.

| axis | edge | window [s] | RMS (deg/s) | rise t90 (ms) | overshoot (%) |
|---|---|---|---|---|---|
| roll | +A | [58.286, 58.685] | 11.23 | 208 | 0.9 |
| roll | -A | [58.785, 59.176] | 23.30 | 268 | -0.1 |
| roll | 0 | [59.276, 60.176] | 7.41 | - | - |
| pitch | +A | [61.785, 62.176] | 11.74 | 212 | -0.1 |
| pitch | -A | [62.276, 62.686] | 21.13 | 263 | 0.9 |
| pitch | 0 | [62.786, 63.686] | 7.52 | - | - |
| yaw | +A | [65.276, 65.687] | 30.61 | 473 | -8.4 |
| yaw | -A | [65.787, 66.185] | 58.35 | - | -17.1 |
| yaw | 0 | [66.285, 67.185] | 17.25 | - | - |

## wdoff_stab_s1 (stabilized)

Truth tilt = angle between body z and world z, max over [release + 1.0 s, release + 2.5 s].

| axis | release [s] | window [s] | max truth tilt (deg) | max abs truth yaw rate (deg/s) |
|---|---|---|---|---|
| roll | 59.141 | [60.141, 61.641] | 0.25 | - |
| pitch | 62.640 | [63.640, 65.140] | 0.20 | - |
| yaw | 66.142 | [67.142, 68.642] | 0.00 | 0.54 |

Whole-run max truth tilt: 21.77 deg at t = 62.59 s, inside the pitch doublet (tilt 19.6 deg in [62.0, 62.5] s, back to 0.06 deg by 64 s). It is not in the yaw window; truth tilt stays at about 0 deg from 66 to 70 s (log runs to 81.2 s, not checked further).

## Notes
- The two runs are not gated on the yaw doublet here; yaw RMS/tilt shown for completeness only, as instructed.
- Edges taken from sticks.csv: first +A/-A/0 sequence per axis (threshold 100 raw).
