# T127 second key: attitude-step metrics, S62 (independent re-implementation)

Status: done. Script: `indi_flight/bench/t127_step_metrics_key.py` (args: flight folder, output md).
Data: `indi_flight/results/stage3_s62/steps_seed{1,2,3}/step_{roll,pitch,yaw}_indi/`.

Method (from the task definition): Euler angle of the stepped axis from `vehicle_attitude` (ZYX),
setpoint from `vehicle_attitude_setpoint`. Yaw unwrapped, median setpoint over window start to
+1.5 s subtracted from both signal and setpoint. Window [t_on, t_on + 3.0 s). Rise 10 to 90 %,
overshoot vs amp, settle 2 % from the last out-of-band sample. Ground truth from
`vehicle_attitude_groundtruth`.

## Step 1: t_on from the setpoint

First setpoint sample >= 50 % of amp after window start. Offset from window start + 2.0 s:
roll +19.5 / +22.8 / +21.2 ms (seeds 1/2/3), pitch +20.0 / +12.8 / +22.8 ms, yaw +13.2 / +21.5 / +22.5 ms.
All nine are 13 to 23 ms late relative to the fixed 2.0 s.

## Steps 2 and 3: metrics

Units: rise [ms], overshoot [%], settle [ms]. "mine fix" = my estimator with t_on = start + 2.0 s
(same convention as the primary). "mine det" = estimator, t_on from setpoint. "truth" = ground
truth with t_on = start + 2.0 s.

| flight | primary (rise / OS / settle) | mine fix | mine det | truth fix | verdict |
|---|---|---|---|---|---|
| seed1 roll | 205 / 0.9 / 358 | 205.0 / 0.94 / 358.2 | 205.0 / 0.94 / 338.8 | 207.5 / 0.78 / 358.2 | AGREE |
| seed1 pitch | 209 / 0.6 / 387 | 208.8 / 0.55 / 387.5 | 208.8 / 0.55 / 367.5 | 211.2 / 0.37 / 388.8 | AGREE |
| seed1 yaw | 550 / 0.2 / 926 | 550.0 / 0.25 / 925.8 | 550.0 / 0.25 / 912.5 | 566.2 / 0.00 / 1018.2 | AGREE |
| seed2 roll | 209 / 0.8 / 394 | 208.8 / 0.81 / 394.0 | 208.8 / 0.81 / 371.2 | 208.8 / 0.63 / 391.5 | AGREE |
| seed2 pitch | 209 / 0.6 / 373 | 208.8 / 0.60 / 372.8 | 208.8 / 0.60 / 360.0 | 211.2 / 0.40 / 370.2 | AGREE |
| seed2 yaw | 540 / 0.6 / 920 | 540.0 / 0.61 / 920.2 | 540.0 / 0.61 / 898.8 | 563.8 / 0.00 / nan | AGREE |
| seed3 roll | 210 / 0.8 / 370 | 210.0 / 0.77 / 370.0 | 210.0 / 0.77 / 348.8 | 211.2 / 0.77 / 2958.8 | AGREE |
| seed3 pitch | 211 / 1.0 / 371 | 211.2 / 0.97 / 371.5 | 211.2 / 0.97 / 348.8 | 210.0 / 0.85 / 370.2 | AGREE |
| seed3 yaw | 551 / 0.5 / 936 | 551.2 / 0.45 / 936.2 | 551.2 / 0.45 / 913.8 | 563.8 / 0.00 / 1028.8 | AGREE |

Notes:
- With t_on = start + 2.0 s, every estimator value is within the tolerance (overshoot +-0.3 pt,
  rise and settle +-5 ms). The largest overshoot gap is 0.05 pt, the largest rise gap 0.2 ms
  and the largest settle gap 0.5 ms (all within the primary's rounding).
- Using the setpoint t_on moves settle by exactly the t_on offset (13 to 23 ms earlier) and leaves
  rise and overshoot unchanged. So the settle figure depends on the t_on convention, and the
  fixed 2.0 s convention is the one that matches the primary.
- Ground truth: rise is 0 to 2.5 ms later for roll and pitch and 13 to 24 ms later for yaw. The
  yaw truth overshoot is 0 and its settle is about 90 ms later than the estimator. Roll and pitch
  settle differ by under 3 ms, except seed3 roll, where the truth never returns to the 2 % band
  until 2.96 s (a steady-state offset in truth, not a rise or overshoot issue). Seed2 yaw truth
  does not settle in the window (nan).
- The primary seed2 metrics.md header says "seed 1" (cosmetic copy error; the rows are seed2 data).

## Verdict

AGREE for the estimator metrics under the primary convention (t_on = start + 2.0 s). The second key
reproduces all 27 INDI values within tolerance. Truth metrics are not in the tolerance check; they
show the expected small offsets, plus a settle artifact on seed3 roll and an unsettled yaw truth
on seed2 yaw.

## A-28 closing test

Window [t_on + 1.5 s, t_on + 3.0 s), t_on = start + 2.0 s. Truth interpolated onto estimator
timestamps for est-truth. Truth settle is against truth's own window mean, band 2 % of amp,
window [t_on, t_on + 3.0 s), time from t_on.

| flight | est-truth mean [deg] | truth-amp [deg] | est-amp [deg] | truth settle vs own final [ms] |
|---|---|---|---|---|
| seed1 roll | +0.236 | -0.242 | -0.007 | 613.2 |
| seed1 pitch | +0.211 | -0.224 | -0.013 | 366.2 |
| seed1 yaw | +0.602 | -0.575 | +0.027 | 920.8 |
| seed2 roll | +0.221 | -0.215 | +0.007 | 584.0 |
| seed2 pitch | +0.223 | -0.230 | -0.008 | 346.5 |
| seed2 yaw | +0.971 | -0.961 | +0.010 | 901.5 |
| seed3 roll | +0.206 | -0.223 | -0.016 | 595.0 |
| seed3 pitch | +0.238 | -0.250 | -0.011 | 656.5 |
| seed3 yaw | +0.785 | -0.713 | +0.070 | 916.2 |

Verdict: yes for seed2 yaw (truth mean sits 0.96 deg below amp, outside the 0.90 deg band, and the
est-truth offset is +0.97 deg, so the truth can never enter the band and the nan follows).
Partly for seed3 roll: the truth mean sits 0.22 deg below amp, leaving 0.08 deg of margin to the
0.30 deg band; the offset alone does not explain the 2.96 s exit, which is an excursion near the
band edge.

Caveat: against its own final value the truth settle is longer for roll and pitch (346 to 656 ms
vs 358 to 392 ms against amp, seed3 roll excluded), because the own-final band is shifted by the 0.2 deg offset. The
own-final settle is not a substitute for the amp-referenced metric.
