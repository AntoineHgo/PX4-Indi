# G5.2 second key (S138), blind independent read

Script: `key2.py` (this directory). Run: `python3 key2.py`. Reads the six run logs
`../{altctl,posctl}_s{1,2,3}/flight.ulg` with pyulog.

Method (per GATES 5b "G5.2 exact test"):
- Edges come from the log: `manual_control_setpoint` (`throttle` = z stick, `pitch` = x stick),
  |value| > 0.05 marks an applied stick. Edge on = first applied sample, release = first centred sample after it.
  Each run has one z step, posctl runs also one x step. The scenario table was not read.
- Truth = `vehicle_local_position_groundtruth` (NED, z down). Start = truth at the on edge (interpolated).
- Final = mean truth over the last 1.0 s of the 6.0 s centred window after release.
- z step: axis = vertical, "up" positive, d = |final - start| in z. Off-axis = max horizontal drift from final.
- x step: axis = horizontal displacement direction from start to final, d = horizontal |final - start|.
  Off-axis = max of perpendicular horizontal and z excursion from final.
- Overshoot = max of (projection beyond final in the step direction) over the centred window, floored at 0.
- Settle = time from release to the last re-entry into |projection - d| <= 2 % of d (the settle band uses the
  step axis only; off-axis is not part of the band). "never" if still outside at the window end.
- Gates: z overshoot <= 0.3 m, x overshoot <= 0.5 m, settle <= 4.0 s, valid if d >= 1.0 m (z) or >= 2.0 m (x).

## Per-run result

| run | step | edge on/off (s) | d (m) | overshoot (m) | settle (s) | off-axis (m) | valid | verdict |
|---|---|---|---|---|---|---|---|---|
| altctl_s1 | z | 58.997 / 60.997 | 1.985 | 0.011 | 1.79 | 0.016 (max horiz drift (m)) | yes | PASS |
| altctl_s2 | z | 59.005 / 60.994 | 1.998 | 0.001 | 2.68 | 0.017 (max horiz drift (m)) | yes | PASS |
| altctl_s3 | z | 58.955 / 60.945 | 1.993 | 0.011 | 1.88 | 0.018 (max horiz drift (m)) | yes | PASS |
| posctl_s1 | z | 58.770 / 60.770 | 2.036 | 0.010 | 1.96 | 0.052 (max horiz drift (m)) | yes | PASS |
| posctl_s1 | x | 66.780 / 69.280 | 4.176 | 0.043 | 1.96 | 0.022 (max perp/z excursion (m)) | yes | PASS |
| posctl_s2 | z | 58.740 / 60.730 | 2.042 | 0.007 | 2.98 | 0.063 (max horiz drift (m)) | yes | PASS |
| posctl_s2 | x | 66.750 / 69.240 | 4.205 | 0.039 | 2.14 | 0.054 (max perp/z excursion (m)) | yes | PASS |
| posctl_s3 | z | 58.832 / 60.832 | 2.020 | 0.026 | 1.20 | 0.068 (max horiz drift (m)) | yes | PASS |
| posctl_s3 | x | 66.843 / 69.332 | 4.170 | 0.063 | 1.89 | 0.063 (max perp/z excursion (m)) | yes | PASS |

Verdict: 9 of 9 steps PASS (no invalid d, no wrong direction). Maximum overshoot 0.063 m (z gate 0.3 m, x gate 0.5 m);
maximum settle 2.98 s (gate 4.0 s).
