# G5.5 offboard probe (S139 flown, S140 scored) and G5.3 mission part

PROBE (RC113: G5 batches before the stage-6 freeze are probes, not gate evidence).
Test: GATES.md 5b "G5.5 exact test" (S139). Stack: INDI rate + INDI position (`params.params`, MC_RATE_CTL_TYPE 1,
MC_INDI_POS_EN 1), quad5in, `--speed 4 --sim v2`, serial (`run_batch.sh`). Score: `summarize.sh` ->
`bench/g55_check.py` (self-test `bench/tests/test_g55_check.py` OK; second key at the freeze) -> `summary.txt`.

## Result

| row | seeds | horiz RMS truth vs analytic [m] (limit 0.5) | vert RMS [m] (limit 0.3) | verdict |
|---|---|---|---|---|
| o1_lemniscate | 1-3 | 0.656-0.666 | 0.079-0.119 | FAIL (horizontal) |
| o2_circle_z | 1-3 | 1.329-1.355 | 0.051-0.056 | FAIL (horizontal) |
| o3_lemniscate_gust | 1-3 | 0.663-0.673 | 0.051-0.096 | FAIL (horizontal) |
| o4_lemniscate_payload | 1-3 | 0.656-0.678 | 0.060-0.113 | FAIL (horizontal) |
| o5_zsine_com_shift | 1-3 | 0.025-0.043 | 0.058-0.093 | PASS |
| o6_zsine_mass | 2-3 | 0.022-0.053 | 0.061-0.065 | PASS (s1 killed rc 143 by a container stop, not re-flown) |
| o7_lemniscate_tau2 | 1-3 | 0.663-0.675 | 0.051-0.104 | FAIL (horizontal) |
| offb_vel_step | 1-3 | vx RMS 0.097-0.102 m/s (0.2), end 0.065-0.079 (0.1), dz 0.026-0.039 m (0.3) | | PASS |

No LOC. Vertical tracking passes everywhere. Every row with a fast horizontal path (lemniscate peak ~4.2 m/s and
up to ~7 m/s^2; circle) fails horizontally by a seed- and disturbance-independent amount: a systematic tracking lag,
not a disturbance effect (gust, payload, tau x2 change nothing). Runner `metrics.json` (window incl. hold) gives
o1 truth 0.58 m against estimate 0.34 m, o2 truth 1.19 m against estimate 0.80 m: about 40 % of the truth error is
estimate-vs-truth lag during motion (pre-t0 static offset 2-3 cm).

O-13 check: these scenarios had never been flown with the reference (PID) stack on quad5in. PID reference flight
`pid_ref/o1_lemniscate_s1` (stock PID, no params file): horizontal RMS 1.04 m, vertical 0.085 m, no LOC (checker
marks it INVALID only for the missing `indi_pos_status`, expected for PID). Scenario flyable; PID also misses 0.5 m.

## Cause (S140, scratch lag script on the o1 s1 logs)

SET-UP FAULT: the batch ran without `--gps-dly/--gnss-delay`, i.e. simulator GNSS latency 0 (`SIM_GZ_GPS_DLY 0`) with
the stock EKF compensation `SENS_GNSS0_DELAY 110` (known, D-s8-gnss-delay in run_scenario.py help). The estimate
then LEADS truth by ~110 ms: truth-minus-estimate x error correlates -0.92 with vx, 0.35 m RMS per axis, est vs truth
0.53 m horizontal RMS (INDI), 0.45 m (PID). Setpoint vs estimate: INDI 0.41 m, PID 0.78 m. This is a mismatched-
compensation plant (a G3 robustness draw), not the nominal plant. Re-fly with matched 110 ms: `../g5_g55_s140_gnss`.
The same mismatch is in every G5 probe flown so far (G5.1-G5.4, G5.7).

Failed attempts kept as metadata: `o1_killed_attempt1` (container prefix collision, renamed x55), `o2_failed_attempt1_s3x`.

## G5.3 mission part (S135 logs, no new flight)

`bench/g53_mission_check.py` (self-test OK) on `results/g5_probe_s135/auto_tour_s{1,2,3}` -> `g53_mission_s*.json`:
all 4 waypoints within 1.0 m (min 0.03-0.80 m), max speed 4.92 m/s <= 5.5 (1.1 x cruise 5): PASS 3/3.

## S140 follow-up (matched GNSS, `../g5_g55_s140_gnss`)
Matched 110 ms: estimate vs truth 0.05 m (fault confirmed and removed), but o1 s1 horiz RMS 0.78 m, o2 s1 0.93 m:
FAIL. The truth now lags the setpoint by 160 ms; the leading estimate had been hiding part of it. Cause: jerk
feed-forward disabled in the module (A18 not implemented). Re-opened: DECISIONS D-A18-REOPEN.
