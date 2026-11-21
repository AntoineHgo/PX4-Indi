# G3 box Q22 (S187): sampler fix, test, regenerated pre-test draws, model check

Owner text: GATES.md "Owner amendments S187" third bullet; QUESTIONS.md Q22 items 2-4. No flight, no commit.

## 1. Sampler change (bench/g3_sample.py, bench/g3_run.py)
- `G1_ERR = (0.8, 1.2)` (was 0.5-2.0); log-uniform per axis. `_nominal_u` now maps e = 1.0 exactly (the log-mid of [0.8, 1.2] is 0.98, so u = 0.5 no longer means nominal).
- Defect found: `model_variant` hook was `tau = scale, tau_up = 1.0, tau_down = asym` and the model hook multiplies, so tau_down = scale x asym (up to 3 x 3 = x9;
  S173 run 17 flew 2.28 x 2.41 = x5.5). `decode()` now: tau draw = SLOW direction, fast = max(slow / asym, 0.5); down slow unless the 10 % inverted draw
  (then up slow). New factors `tau_up`, `tau_down` (absolute x nominal); `tau_asym.value` = realised tau_down/tau_up, `tau_asym.drawn_ratio` = drawn |slow/fast|.
  Hook: `tau = slow, tau_up = tau_up/slow, tau_down = tau_down/slow` (multipliers on tau). `bench/model_variant.py` needed no change (it only multiplies).
- Corners C1/C2/C4 pin u at the range ends, so they follow the new range: e 1.2 / 0.8 / 1.2 (no table edit needed). C1 tau x3 and C5 tau x0.5 are the slow-direction draw.
- `g3_run.py`: tau_asym `via` check and accounting of the two new factors (it asserts every factor is accounted for).
- Seeds: u-vector draws unchanged, so same seed -> same values for every other factor (verified on the 20 draws: only g1_err, g1_ratio,
  g1_ctrl_mult and the tau/asym block differ; tau_scale value itself is unchanged, it now means the slow side). The old sampler reproduces the 20 S173 g3_draw.json factor blocks exactly.
  Pre-fix files are not byte-compatible (new keys).

## 2. Tests (bench/tests/test_g3_sample.py)
New `test_q22_box_2000_draws`: 2000 free draws, e in [0.8, 1.2] per axis, tau_up and tau_down in [0.5, 3], slow == tau_scale, inverted ~10 %, floor exercised, corner values 1.2/0.8/1.2 for C1/C2/C4.
Updated to the new box: test_ranges (also checks tau_up/down hook products), LHS range list, corner pins (2.0->1.2, 0.5->0.8), pretest x_asym, decode-law checks (drawn_ratio).
Run: `python3 bench/tests/test_g3_sample.py` -> 14 PASS, failures: 0. `python3 bench/tests/test_g3_run.py` -> all PASS.
Break check: restored `tau_down = tau * asym` (t_up, t_dn = 1.0, tau * asym when not inverted) -> FAIL test_pretest_set, test_q22_box_2000_draws, test_ranges (failures: 3). Fix restored, failures: 0.

## 3. Pre-test draws (pretest_draws/, JSON only)
Same as S173: `python3 bench/g3_sample.py campaign 173 --n 300 --out DIR`, first 20 runs (idx 0-19, LHS; the S173 pre-test is the first 20 draws of the campaign, see
results/g3_pretest_s173/fly.sh) + index.json trimmed to 20. All 20 draws changed (every run has new e on 3 axes and new tau_up/tau_down); other factors, modes and seeds are identical.
Run 17: old draw e roll/pitch/yaw 0.85/1.52/1.70, tau up/down 2.28/5.49 (x nominal); new draw (same u point, new map) 0.93/1.11/1.14, tau_up/tau_down 0.95/2.28. The S173 flight of run 17 (e 1.52) is out of box: reported with both stacks' values, not part of the re-flown set.
Note: the old e = 1.52 of run 17 is out of the new [0.8, 1.2] box.

| run | e roll/pitch/yaw old -> new | tau slow old -> new (x nom) | tau_up/tau_down old -> new |
|---|---|---|---|
| 0 | 1.05/0.70/1.18 -> 1.00/0.88/1.03 | 0.79 -> 0.79 | 0.79/1.26 -> 0.50/0.79 |
| 1 | 0.59/1.03/0.72 -> 0.84/0.99/0.89 | 0.92 -> 0.92 | 0.92/2.69 -> 0.50/0.92 |
| 2 | 0.59/1.10/1.85 -> 0.84/1.01/1.17 | 1.31 -> 1.31 | 1.31/3.05 -> 0.56/1.31 |
| 3 | 0.71/1.93/1.58 -> 0.89/1.19/1.12 | 2.79 -> 2.79 | 2.79/3.22 -> 2.43/2.79 |
| 4 | 0.59/0.54/0.56 -> 0.84/0.82/0.83 | 1.93 -> 1.93 | 1.93/4.20 -> 0.88/1.93 |
| 5 | 0.56/1.05/0.75 -> 0.83/0.99/0.90 | 1.41 -> 1.41 | 1.41/2.60 -> 0.77/1.41 |
| 6 | 0.66/0.77/1.78 -> 0.87/0.91/1.16 | 0.69 -> 0.69 | 0.69/0.80 -> 0.59/0.69 |
| 7 | 1.01/1.79/0.84 -> 0.98/1.16/0.93 | 1.36 -> 1.36 | 1.36/3.08 -> 0.60/1.36 |
| 8 | 0.64/0.69/1.01 -> 0.86/0.88/0.98 | 0.58 -> 0.58 | 0.58/1.45 -> 0.50/0.58 |
| 9 | 1.33/1.04/0.66 -> 1.07/0.99/0.87 | 1.69 -> 1.69 | 1.69/2.35 -> 1.22/1.69 |
| 10 | 1.51/1.40/0.90 -> 1.10/1.08/0.95 | 1.08 -> 1.08 | 1.08/1.44 -> 0.81/1.08 |
| 11 | 1.31/1.17/0.57 -> 1.06/1.03/0.83 | 0.99 -> 0.99 | 0.99/2.34 -> 0.50/0.99 |
| 12 | 1.78/1.65/0.96 -> 1.16/1.13/0.97 | 0.54 -> 0.54 | 0.54/1.01 -> 0.50/0.54 |
| 13 | 1.73/1.08/1.07 -> 1.15/1.00/1.00 | 1.40 -> 1.40 | 1.40/3.45 -> 0.57/1.40 |
| 14 | 0.73/1.14/0.54 -> 0.89/1.02/0.82 | 1.26 -> 1.26 | 1.26/2.20 -> 0.72/1.26 |
| 15 | 1.27/0.82/0.82 -> 1.05/0.93/0.93 | 0.57 -> 0.57 | 0.57/1.49 -> 0.50/0.57 |
| 16 | 0.89/1.46/1.55 -> 0.95/1.09/1.11 | 0.84 -> 0.84 | 0.84/2.51 -> 0.50/0.84 |
| 17 | 0.85/1.52/1.70 -> 0.93/1.11/1.14 | 2.28 -> 2.28 | 2.28/5.49 -> 0.95/2.28 |
| 18 | 0.50/0.52/1.51 -> 0.80/0.81/1.10 | 1.28 -> 1.28 | 1.28/3.09 -> 0.53/1.28 |
| 19 | 1.82/1.13/1.57 -> 1.17/1.01/1.12 | 1.06 -> 1.06 | 1.06/3.02 -> 0.50/1.06 |

## 4. Model check (bench/g3_box_margins.py -> margins_tables.md)
Model margins_models.L_indi (rate) / L_att_indi (attitude), glue g3_osc_margins.cfg: K 20, ACT_TC 0.033, MC_ROLL/PITCH_P 8, measured path, 800 Hz, g = 1/e.
Gains = freeze-9 = firmware/bench defaults `bench/params/quad5in_indi_defaults.params` as in the S173 base `results/g5_freeze_s157/params.params` (I found no separate freeze-9 params file; same K/ACT_TC/G1). Yaw, outer loops, weak motor, sag not modelled; asymmetric tau enters as one linear tau (slow, or mean of up/down).
PM deg / GM dB @ crossover Hz; n = 1 + telemetry frames.

## Fast-motor corner (tau both directions x tau, loop delay 10 ms)
| e | tau x | delay ms | n=1+tel frames | rate PM deg / GM dB @Hz | att PM / GM @Hz |
|---|---|---|---|---|---|
| 0.8 | 0.5 | 10 | 1 | 54/4.2 @7.63 | 75/17.8 @1.22 |
| 0.8 | 0.5 | 10 | 4 | 63/4.9 @7.35 | 75/20.4 @1.22 |
| 0.8 | 1.0 | 10 | 1 | 58/7.3 @5.05 | 74/16.1 @1.25 |
| 0.8 | 1.0 | 10 | 4 | 64/8.4 @4.86 | 73/17.1 @1.26 |
| 1.0 | 0.5 | 10 | 1 | 78/7.8 @4.18 | 74/19.1 @1.24 |
| 1.0 | 0.5 | 10 | 4 | 83/8.6 @3.87 | 74/20.8 @1.25 |
| 1.0 | 1.0 | 10 | 1 | 67/10.7 @3.39 | 72/14.9 @1.29 |
| 1.0 | 1.0 | 10 | 4 | 70/12.4 @3.24 | 72/15.4 @1.30 |
| 1.2 | 0.5 | 10 | 1 | 78/11.4 @2.86 | 73/18.3 @1.26 |
| 1.2 | 0.5 | 10 | 4 | 81/12.1 @2.70 | 73/19.3 @1.28 |
| 1.2 | 1.0 | 10 | 1 | 66/14.0 @2.58 | 70/13.3 @1.33 |
| 1.2 | 1.0 | 10 | 4 | 69/16.3 @2.48 | 70/13.5 @1.35 |

## 20 box pre-test draws (roll, pitch)
| run | axis | e | tau up/down ms | delay ms | n=1+frames | rate PM slow/mean | att PM slow/mean | <30 |
|---|---|---|---|---|---|---|---|---|
| 0 | roll | 1.00 | 16/26 | 7.50 | 4 | 78/82 | 72/72 |  |
| 0 | pitch | 0.88 | 16/26 | 7.50 | 4 | 76/79 | 73/73 |  |
| 1 | roll | 0.84 | 16/30 | 8.75 | 2 | 66/67 | 73/74 |  |
| 1 | pitch | 0.99 | 16/30 | 8.75 | 2 | 71/75 | 72/73 |  |
| 2 | roll | 0.84 | 19/43 | 1.25 | 4 | 75/82 | 69/70 |  |
| 2 | pitch | 1.01 | 19/43 | 1.25 | 4 | 74/82 | 67/69 |  |
| 3 | roll | 0.89 | 80/92 | 1.25 | 2 | 57/59 | 59/61 |  |
| 3 | pitch | 1.19 | 80/92 | 1.25 | 2 | 53/54 | 45/49 |  |
| 4 | roll | 0.84 | 29/64 | 10.00 | 4 | 57/62 | 69/72 |  |
| 4 | pitch | 0.82 | 29/64 | 10.00 | 4 | 57/61 | 69/72 |  |
| 5 | roll | 0.83 | 25/47 | 0.00 | 2 | 73/78 | 68/69 |  |
| 5 | pitch | 0.99 | 25/47 | 0.00 | 2 | 72/78 | 67/68 |  |
| 6 | roll | 0.87 | 20/23 | 1.25 | 1 | 82/83 | 71/71 |  |
| 6 | pitch | 0.91 | 20/23 | 1.25 | 1 | 83/85 | 71/71 |  |
| 7 | roll | 0.98 | 20/45 | 7.50 | 3 | 66/73 | 69/71 |  |
| 7 | pitch | 1.16 | 20/45 | 7.50 | 3 | 64/71 | 67/70 |  |
| 8 | roll | 0.86 | 16/19 | 10.00 | 3 | 70/71 | 74/75 |  |
| 8 | pitch | 0.88 | 16/19 | 10.00 | 3 | 73/73 | 74/74 |  |
| 9 | roll | 1.07 | 40/56 | 0.00 | 3 | 68/71 | 64/65 |  |
| 9 | pitch | 0.99 | 40/56 | 0.00 | 3 | 69/72 | 65/66 |  |
| 10 | roll | 1.10 | 27/36 | 3.75 | 3 | 74/77 | 68/69 |  |
| 10 | pitch | 1.08 | 27/36 | 3.75 | 3 | 74/77 | 69/69 |  |
| 11 | roll | 1.06 | 16/33 | 8.75 | 2 | 70/75 | 71/72 |  |
| 11 | pitch | 1.03 | 16/33 | 8.75 | 2 | 70/75 | 71/73 |  |
| 12 | roll | 1.16 | 16/18 | 8.75 | 3 | 81/81 | 73/73 |  |
| 12 | pitch | 1.13 | 16/18 | 8.75 | 3 | 81/82 | 73/73 |  |
| 13 | roll | 1.15 | 19/46 | 5.00 | 2 | 65/73 | 66/69 |  |
| 13 | pitch | 1.00 | 19/46 | 5.00 | 2 | 67/74 | 68/70 |  |
| 14 | roll | 0.89 | 24/41 | 5.00 | 2 | 69/73 | 70/71 |  |
| 14 | pitch | 1.02 | 24/41 | 5.00 | 2 | 69/74 | 69/70 |  |
| 15 | roll | 1.05 | 16/19 | 5.00 | 3 | 86/87 | 72/72 |  |
| 15 | pitch | 0.93 | 16/19 | 5.00 | 3 | 85/86 | 72/72 |  |
| 16 | roll | 0.95 | 16/28 | 5.00 | 1 | 75/79 | 72/72 |  |
| 16 | pitch | 1.09 | 16/28 | 5.00 | 1 | 76/80 | 71/71 |  |
| 17 | roll | 0.93 | 31/75 | 1.25 | 3 | 62/69 | 62/66 |  |
| 17 | pitch | 1.11 | 31/75 | 1.25 | 3 | 59/67 | 57/64 |  |
| 18 | roll | 0.80 | 17/42 | 6.25 | 3 | 66/70 | 71/72 |  |
| 18 | pitch | 0.81 | 17/42 | 6.25 | 3 | 66/70 | 71/72 |  |
| 19 | roll | 1.17 | 16/35 | 5.00 | 2 | 71/77 | 69/70 |  |
| 19 | pitch | 1.01 | 16/35 | 5.00 | 2 | 73/79 | 70/71 |  |

Worst PM over draws (slow or mean tau, rate or att): 44.9 deg, run 3 pitch


Reading: fast-motor corner (e 0.8, tau x0.5, 10 ms) rate loop PM 54 deg with n=1 (63 at n=4), GM only 4.2 dB at 7.6 Hz (the tight number); e 1.2 same tau/delay: rate PM 78, GM 11.4 dB; att PM 73-75.
No draw below 30 deg PM; worst is run 3 pitch (slow tau 92 ms, e 1.19): rate 53, att 45.

## 5. Reproduce
```
cd indi_flight
python3 bench/tests/test_g3_sample.py && python3 bench/tests/test_g3_run.py
python3 bench/g3_sample.py campaign 173 --n 300 --out /tmp/c173   # then copy run_000..019.json + index.json (trim to 20)
python3 bench/g3_box_margins.py results/g3_box_s187/margins_tables.md
```
