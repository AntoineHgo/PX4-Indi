# Second key K100: G2 rate-loop margins (S100)

## Method
Script `bench/second_key_m3a_s100.py --axis N` (copy of the s41 second key, only the torque_sp index made selectable: inject[N], torque_sp[N] = u after injection, torque_sp_pre_inject[N] = c before). It reads `indi_rate_status` from each flight.ulg, takes the full injection window (first to last nonzero inject), forms direct Fourier sums at the 18 log-spaced bins (1 to 50 Hz) and L = -Y/X with Y = pre-injection and X = post-injection torque. PM and crossover come from the first downward 0 dB crossing, GM from the next -180 deg phase crossing, DM = PM/(360 fc). Compared values are the full-window variant A, which is the same estimator family as the primary; variants B1 (periods 2-3) and B2 (per-period averaged) were also run (all AGREE with the script's own bin tolerances, per-flight output in the scratchpad, not archived). Axis: roll 0, pitch 1, yaw 2. Tolerance: GM 1 dB, PM 3 deg, DM 10 %.

## Results (primary / key / delta)
| flight | GM dB | PM deg | DM ms | f_c Hz | agree |
|---|---|---|---|---|---|
| roll800_s1 | 15.89 / 15.87 / -0.02 | 68.19 / 68.32 / +0.13 | 46.2 / 46.5 / +0.5 % | 4.097 / 4.083 / -0.014 | yes |
| roll800_s2 | 15.81 / 15.71 / -0.10 | 68.70 / 68.31 / -0.39 | 46.3 / 46.1 / -0.4 % | 4.120 / 4.113 / -0.007 | yes |
| roll400_s1 | 13.12 / 13.21 / +0.09 | 70.02 / 69.59 / -0.43 | 50.1 / 50.2 / +0.1 % | 3.880 / 3.853 / -0.027 | yes |
| roll400_s2 | 13.23 / 13.24 / +0.01 | 70.00 / 69.96 / -0.04 | 50.8 / 50.9 / +0.1 % | 3.827 / 3.821 / -0.006 | yes |
| pitch800_s2 | 16.05 / 16.05 / -0.00 | 68.84 / 68.59 / -0.25 | 46.1 / 46.4 / +0.6 % | 4.149 / 4.111 / -0.038 | yes |
| pitch400_s1 | 13.32 / 13.36 / +0.04 | 70.15 / 69.82 / -0.33 | 51.0 / 50.7 / -0.5 % | 3.823 / 3.826 / +0.003 | yes |
| pitch400_s2 | 13.16 / 13.15 / -0.01 | 70.50 / 70.18 / -0.32 | 50.3 / 50.3 / -0.0 % | 3.895 / 3.878 / -0.017 | yes |
| yaw800_s1 | 21.53 / 21.51 / -0.02 | 87.13 / 87.19 / +0.06 | 154.6 / 155.5 / +0.5 % | 1.565 / 1.558 / -0.007 | yes |
| yaw800_s2 | 21.27 / 21.30 / +0.03 | 86.97 / 86.96 / -0.01 | 153.4 / 154.2 / +0.5 % | 1.575 / 1.567 / -0.008 | yes |
| yaw400_s2 | 16.17 / 16.26 / +0.09 | 86.54 / 86.74 / +0.20 | 161.2 / 161.5 / +0.2 % | 1.491 / 1.492 / +0.001 | yes |
| P1 (pitch800 s1) | 15.73 / 15.76 / +0.03 | 68.98 / 68.49 / -0.49 | 46.2 / 46.4 / +0.3 % | 4.146 / 4.103 / -0.043 | yes |
| P2 (yaw400 s1) | 15.51 / 15.64 / +0.13 | 86.99 / 86.97 / -0.02 | 163.6 / 163.8 / +0.1 % | 1.477 / 1.475 / -0.002 | yes |

## Verdict
12/12 flights agree. Worst absolute deltas: GM 0.13 dB, PM 0.49 deg, DM 0.6 %, f_c 0.043 Hz. Flights failing the gate under the key (GM>=6, PM>=45, DM>=2 control periods at 400 Hz, the more demanding rate): none.

## Unverified / caveats
- Not independent of the data: same ulog, same injection signals, same estimator family; it checks the primary implementation (indexing, windowing, margin extraction), not the plant or the injection design.
- No s41 self-test exists in bench/tests; none was written or extended. Roll (axis 0) reproduces the s41 behaviour only by construction (default axis 0, code otherwise unchanged); the axis 1/2 index change is exercised only by these runs, and the field names were checked in a yaw log.
- DM was computed as PM/(360 fc), not extracted independently from a delay model. Telemetry latency assumed 0 frames. 2T = 2.5 ms (800 Hz) or 5 ms (400 Hz); all DM are above 45 ms.
- Per-flight variant tables (B1, B2) are not archived in the results dir.
