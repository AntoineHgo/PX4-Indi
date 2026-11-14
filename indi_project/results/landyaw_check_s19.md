# Landed yaw-filter fix: effect on the metric windows (session 19)

Firmware 1d776dc6dc (D-landyaw) vs the committed frozen-candidate runs (pre-fix), INDI tuned (r4f/c00), same seeds.
Log `landyaw_check_s19.log`, metrics `landyaw_check_s19/<scenario>/indi_tuned/seed*/metrics.json`.
Values are post-fix / pre-fix.

| scenario | seed | roll deg rms | pitch deg rms | yaw deg rms | roll rate rad/s rms |
|---|---|---|---|---|---|
| step_diag (x4) | 1 | 3.82 / 3.76 | 4.22 / 4.16 | 1.06 / 1.05 | 0.182 / 0.180 |
| step_diag (x4) | 2 | 3.90 / 3.87 | 4.29 / 4.25 | 1.01 / 1.03 | 0.176 / 0.176 |
| step_diag (x4) | 3 | 4.05 / 3.79 | 4.43 / 4.18 | 1.03 / 1.09 | 0.174 / 0.183 |
| com_shift | 1 | 0.0745 / 0.0718 | 0.0496 / 0.0478 | 0.0317 / 0.0292 | 0.0121 / 0.0124 |
| com_shift | 2 | 0.0598 / 0.0709 | 0.0535 / 0.0564 | 0.0345 / 0.0345 | 0.0121 / 0.0122 |
| com_shift | 3 | 0.0697 / 0.0729 | 0.0560 / 0.0481 | 0.0311 / 0.0305 | 0.0123 / 0.0122 |

Differences are a few percent with both signs (largest: com_shift seed 2 roll -16 %, seed 3 pitch +16 %, at
hundredths of a degree), the same size as run-to-run variation for identical inputs (D-hovernoise), and far smaller
than the INDI/PID ratios they would have to move (com_shift 0.15x, step_diag 0.92x). Conclusion: the fix acts only
before the metric windows; the frozen benchmark results stand for the fixed firmware. Not checked: takeoff yaw
behaviour itself (outside every window), other scenarios.
