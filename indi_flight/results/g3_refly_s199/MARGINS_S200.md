# S200: linear rate-loop margins on the drawn plants of failed G3 runs 245 / 239 / 283, and controller ACT_TC sweep

Method. Model `bench/margins_models.py` (L_indi, L_att_indi), margins via `margins_est.margins`; config and margin reading reused from `bench/g2_rate_model_s165.py` (cfg, flown freeze params: K 20, MC_INDI_ACT_TC 0.033, LEAD 1 -> c = min(K tau_m, 2), ACT_BLD 1 s, MC_ROLL/PITCH_P 8, measured torque path meas=True, 800 Hz because `--rate-hz 800` in run.json argv and the freeze params; nominal plant tau 33 ms from `sim/models/quad5in/model.sdf`). Plant glue as in `bench/g3_osc_margins.py` (g = 1/e with e from `g3_draw.json` realised controller/plant G1, lat_s = act + imu delay, n = 1 + eRPM latency frames); g3_box_margins.py / g3_osc_margins.py only tabulate the 20 pre-test draws, so the three failed draws and the tau_m sweep are new: `cause_s199/margins_s200.py` (data `margins_s200.json`). Asymmetric tau enters as one linear tau: slow = max(up, down), mean = (up+down)/2 (mean results within 1-4 deg PM of slow, so only slow is tabulated). Three loops: **rate** = rate loop alone (M3a break, att_p 0); **rate+att** = M3a break with the attitude path closed (what the G2 rate cells measure); **att** = attitude loop (break at rate setpoint). Margins read as in G2: PM min over downward crossings, GM min over -180 deg crossings (signed, negative = |L| > 1).

Self-test (`python3 cause_s199/margins_s200.py`): (1) synthetic L = wc/s e^{-sTd} gives PM 61.35 deg, OK. (2) nominal flown roll 800 Hz: model 56 deg / 18.0 dB / 3.50 Hz vs measured S160 mean 56.4 deg / 18.9 dB / 3.27 Hz, within tolerance (PM 10 deg, GM 3 dB): OK. (3) cfg() reproduces the S165 cfg exactly: OK. (4) G2_SCORES.md freeze-10 has only one rate cell, roll800_fwdef_s2 (46.9 deg / 15.7 dB / 75.5 ms, a different firmware-default config: K x0.5, ACT_TC 0.05, model path). The model gives 61 deg / 17.3 dB / 89 ms: GM within 1.6 dB, PM +14 deg, so it only passes at a loose PM tolerance of 20 deg (S165 already saw +11.6 deg on this cell). The flown nominal config is not in G2_SCORES, hence check (2) against S160.

## 1. Drawn plants of the failed runs (slow tau, ACT_TC 0.033, Tb 1 s; PM deg / GM dB / DM / crossover)

| run (axis) | drawn: e, tau up/down, delay, tel frames | nominal plant rate / rate+att / att | drawn: rate | drawn: rate+att | drawn: att |
|---|---|---|---|---|---|
| 245 pitch | 1.20, 99/86 ms (x3/x2.6), 10 ms, 3 | 79/18.4/65 ms@3.39 Hz ; 56/18.0/45 ms@3.50 ; 69/17.0/152 ms@1.25 | 44 / 24.9 / 68 ms @1.78 Hz | **6** / 24.9 / 7.5 ms @2.11 Hz | 24 / **3.1** / 34 ms @1.95 Hz |
| 239 roll | 1.18, 61/84 ms (x1.85/x2.55), 7.5 ms, 3 | same | 49 / 24.5 / 72 ms @1.92 Hz | **13** / 24.5 / 16 ms @2.23 Hz | 43 / **5.3** / 67 ms @1.77 Hz |
| 283 pitch | 0.88, 16.5/16.5 ms (x0.5), 10 ms, 1 | same | 71 / **6.2** / 35 ms @5.68 Hz | 61 / **6.1** / 32 ms @5.29 Hz | 75 / 19.5 / 169 ms @1.23 Hz |

Model |L| and phase at the frequency seen in the log (slow tau; log estimate from CAUSE_S199.md in the last column):

| run | f Hz | rate | rate+att | att | log estimate |
|---|---|---|---|---|---|
| 245 | 2.0 | 0.84 at -139 | 1.10 at -174 | 0.96 at -159 | 0.91 at -145 (rate loop) |
| 239 | 2.0 / 2.5 | 0.94 at -132 / 0.67 at -137 | 1.22 at -167 / 0.81 at -168 | 0.88 at -149 / 0.61 at -174 | 0.88 at -147 (2-2.5 Hz) |
| 283 | 10.75 | 0.63 at -153 | 0.61 at -157 | 0.10 | 0.92 at -176 |

Reading: the rate loop alone is not near PM 0 on any of the three plants (PM 44 / 49 / 71 deg). Its crossover moves to 1.8-1.9 Hz on the slow plants (tau x2.6-3 lowers the loop gain bandwidth), so a 2 Hz line is at the rate-loop crossover, and |L| 0.84-0.94 at -132..-139 deg reproduces the logged 0.88-0.91 at -145..-147 deg to about 0.1 in gain and 10 deg in phase. With the attitude path closed (MC_ROLL/PITCH_P 8, still no position loop) the model gives PM 6 deg (245) and 13 deg (239) at 2.1-2.2 Hz, |L| > 1 at -167..-174 deg at 2 Hz, and an attitude-loop GM of only 3.1 / 5.3 dB at 2.3-2.6 Hz.

## 2. Controller ACT_TC (tau_m) sweep over the box corners

Corners: plant tau x0.5 / x3 (symmetric, of 33 ms), delay 0 / 10 ms, telemetry frames 0 / 3, e (controller G1 / plant G1) two values, pitch axis, firmware lead c = min(20 tau_m, 2). Worst case over 16 corners, PM deg / GM dB (negative = unstable-type).

**(a) e = 0.5 / 2 as requested**

| tau_m s | rate | rate+att | att | min of three PM |
|---|---|---|---|---|
| 0.017 | 2.3 / 0.2 | -16.5 / -10.0 | -95.5 / -6.4 | -95.5 |
| 0.025 | -12.4 / -0.9 | -13.6 / -7.7 | -26.8 / -4.5 | -26.8 |
| 0.033 | -25.9 / -1.9 | -27.1 / -5.5 | -16.2 / -2.8 | -27.1 |
| 0.05 | -50.6 / -3.8 | -51.9 / -3.8 | 3.5 / 0.6 | -51.9 |
| 0.07 | -74.2 / -5.5 | -75.7 / -5.6 | 21.7 / 4.3 | -75.7 |
| 0.1 | -102.3 / -7.6 | -103.8 / -7.7 | 40.0 / 8.4 | -103.8 |

No tau_m gives positive worst-case PM on all loops. The corners are split: low e (plant gain x2, fast tau, 10 ms) kills the rate loop and gets worse as tau_m (and lead) grows (rate at e = 2 is +25..+64 deg everywhere); high e with slow tau, 10 ms, 3 frames kills the attitude loop and gets better with tau_m. The best worst-case across loops is tau_m = 0.025 (-26.8 deg), 0.033 is -27.1: no real difference, both negative.

**(b) e = 0.8 / 1.2 (the realised G3 range)**. The 300 campaign draws have e in [0.80, 1.20], tau x0.5..3, delay 0..10 ms, frames 0..3 (checked on g3_draw.json), so e = 0.5 / 2 is outside the box actually drawn.

| tau_m s | rate | rate+att | att | min PM | worst corner (rate+att) |
|---|---|---|---|---|---|
| 0.017 | 32.7 / 6.9 | -4.0 / -4.1 | -5.5 / -0.7 | -5.5 | tau x3, 10 ms, e 1.2, 3 fr |
| 0.025 | 37.9 / 5.4 | 0.9 / 1.2 | 10.3 / 1.3 | 0.9 | same |
| 0.033 | 42.8 / 4.2 | 5.7 / 4.0 | 24.1 / 3.1 | 5.7 | same (GM at tau x0.5, e 0.8) |
| **0.05** | 26.7 / 2.0 | **15.3 / 1.8** | 44.2 / 6.5 | **15.3** | same |
| 0.07 | -1.5 / -0.1 | -2.9 / -0.2 | -126 (wrap artefact, see below) / -2.4 | -126 | tau x0.5, 10 ms, e 0.8, 0 fr |
| 0.1 | -34.6 / -2.5 | -36.1 / -2.6 | 60.6 / 12.3 | -36.1 | same |

tau_m = 0.05 maximises the worst-case PM (15 deg, rate+att, versus 5.7 deg at 0.033) on the realised box, and it is the best of the six on rate+att; the rate loop alone prefers 0.033 (43 vs 27 deg) and the attitude loop prefers 0.1 (61 vs 44 deg, but 0.1 and 0.07 break the fast-plant corner). Worst GM is still only 1.8-2.0 dB at 0.05 (fast-plant corner), and none of the corners reaches the G2 limits (PM 45 / GM 6 dB). The att -126 deg at 0.07 is a mis-read of a wrapped phase crossing in a corner that is already unstable by the rate loop; treat as unstable. The same sweep with the lead frozen at 0.66 (only the model time constant changed) is in `margins_s200.json` (`sweep_lead066`): worst-case PM stays -26 deg for rate and rate+att at every tau_m, so the lead gain c = K tau_m, not tau_m itself, is what moves the margin in the e = 0.5/2 box.

On the three drawn plants tau_m 0.05 instead of 0.033: 245 rate+att PM 6 -> 15 deg, att GM 3.1 -> 6.5 dB; 239 rate+att 13 -> 23 deg, att GM 5.3 -> 8.6 dB; 283 rate+att 61 -> 47 deg, GM 6.1 -> 3.6 dB (crossover 8.3 Hz, DM 16 ms). So 0.05 helps the two slow-plant runs and costs the fast-plant run.

## Conclusions

**Shown by the model**
- On the 245 and 239 plants the rate loop plus attitude path (no position loop) has PM 6 deg and 13 deg at 2.1-2.2 Hz and the attitude loop GM is 3-5 dB. The model |L| and phase at 2 Hz match the logged describing-function values to about 0.1 and 10 deg. The 2 Hz mode is therefore reproduced by rate + attitude with the drawn slow tau (x2.6-3), delay 7.5-10 ms and 3 telemetry frames; it does not need the position loop to be near instability. The rate loop alone has PM 44-49 deg and crossover 1.8-1.9 Hz.
- 283: the rate loop on the fast plant (tau 16.5 ms) loses gain margin, not phase margin: GM 6.2 dB (phase crossing 13.9 Hz), PM 71 deg, crossover 5.7 Hz. The model |L| at 10.75 Hz is 0.63 at -153 deg, about 3.3 dB below the logged 0.92 at -176 deg.
- On the realised box (e 0.8-1.2) ACT_TC 0.05 gives the best worst-case PM (15 deg) of the six values; 0.033 gives 5.7 deg. No value reaches PM 45 deg / GM 6 dB at every corner: slower tau_m helps slow-plant corners and hurts fast-plant corners, because the lead gain c = K tau_m rises with it.

**Not shown / outside the model**
- 283 at 10.75 Hz: the model does not reach |L| = 1 there. Missing 3 dB is not explained by e = 0.88 and tau 16.5 ms alone; candidates (vibration x5, 20 % eRPM dropout, the measured-path eta, notch/filter settings, motor tau up/down split) are not in the linear model. Whether delays 5+5 ms are really lumped as command latency is an assumption (g3_osc_margins glue).
- Position loop, saturation, thrust sag, dropout/freeze, inertia scale, gust triggers, and growth rate of the nonlinear plateau (29 deg / 360 dps in 245) are not modelled; PM near 0 in the model gives a lightly damped mode, not the exponential growth seen from lift-off.
- A tau_m change was only evaluated on the linear loop; no flight, no check of the weak-motor path (blend), yaw, or hover thrust ranges. The e = 0.5 / 2 box asked for is outside the realised G3 box; there the worst corner is unstable for every tau_m.
- Flown parameters assumed from the freeze params + run `g3_params.txt` (ACT_TC 0.033, K 20, ACT_BLD 1.0, LEAD 1, ERPM_DLY 1), MC_ROLL/PITCH_P 8 from the airframe file, gyro/dgyro cutoffs 40/20 Hz (unverified vs IMU params, as in S165); I did not read the flight log params or the 4040 file for the actual run. Tb 1 s changes margins by < 0.1 deg (blend acts below 0.2 Hz).
