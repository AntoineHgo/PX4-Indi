# G3 pre-test limit cycle vs linear margins (S186, analysis only)

Scripts: `bench/g3_osc_margins.py` (glue + self-test, tables), `bench/g3_osc_sweep.py` (knob sweep). Full 20-run table: `tables.md`.
Model: `margins_models.L_indi` (rate loop) and `L_att_indi` (attitude loop, exists already: P closed around the closed rate loop,
MC_PITCH_P 8). Flight config: K 20, ACT_TC 0.033 (lead c = 0.66), measured path, 800 Hz. My glue only: g = 1/e, rotor tau = 33 ms x
tau_scale x (asym | mean of 1 and asym), lat_s = loop_delay total_ms, n = 1 + tel frames.

## Result 1: attitude loop at the drawn plants (axis, PM deg / crossover Hz, slow = tau_down, mean = tau mean)
| run | axis | e | tau up/down ms | att PM slow | att PM mean | observed |
|---|---|---|---|---|---|---|
| nominal | - | 1 | 33/33 | 69 @1.25 | 69 | - |
| 3 | pitch | 1.93 | 92/106 | -1.5 @1.7 | 2 | OSC |
| 7 | pitch | 1.79 | 45/102 | -0.6 @1.8 | 20 | OSC |
| 13 | roll | 1.73 | 46/114 | -2 @1.8 | 20 | OSC |
| 17 | pitch | 1.52 | 75/181 | -16 @1.6 | 2.5 | OSC |
| 12 | roll/pitch | 1.78/1.65 | 18/33 | 60/63 | 65/66 | stable |
| 19 | roll | 1.82 | 35/100 | 2 @1.8 | 28 | not reported osc (unchecked) |
The other 34 axis-runs: att PM 23 (run 17 roll) to 74 deg (slow) and 48 to 75 (mean). Rate loop alone: PM 36-79 deg on every
drawn run (run 17 pitch 36 deg slow, 42 mean, crossover 1.2 Hz); the rate loop is NOT the problem. Unstable crossings sit at 1.6-1.8 Hz,
the observed frequency.

## Result 2: 2x2 over the 40 axis-runs (att PM < 15 deg, slow tau)
| | observed osc | not osc |
|---|---|---|
| predicted unstable/marginal | 4 | 1 (run 19 roll) |
| predicted OK | 0 | 35 |
With mean tau and threshold PM < 25 deg: 4 / 0 / 0 / 36 (7 pitch and 13 roll are 20 deg, i.e. the asymmetry choice matters).

## Result 3: stability boundary (delay 10 ms, 2 telemetry frames), attitude PM deg, rows e, columns rotor tau x33 ms (down value)
| e \ tau | 0.5 | 1 | 2 | 3 | 6 | 9 |
|---|---|---|---|---|---|---|
| 0.5 | 76 | 76 | 74 | 72 | 58 | 22 |
| 1.0 | 74 | 72 | 65 | 50 | -4 | -24 |
| 1.5 | 71 | 66 | 41 | 11 | -25 | -40 |
| 2.0 | 66 | 54 | 14 | -9 | -37 | -48 |
Boundary (PM 0): roughly e x tau_mult >= 5 (e 2 at tau x2.7, e 1.5 at x3.5, e 1 at x5). PM < 30 once e x tau_mult >~ 3.5. The G3 box
(e to 2, tau to 3, asym to 3 => down value to 9x) is mostly outside it at the high-e / slow-motor corner.
Separate corner: rate loop alone is unstable at e 0.5, tau x0.5, 10 ms (PM -22; high frequency, not the observed mode).

## Result 4: single knob to get attitude PM >= 30 at e 2, tau x3, 10 ms (min over the e 0.5..2, tau 0.5..3 box)
| knob | value | worst att PM | nominal (e 1, no delay) |
|---|---|---|---|
| MC_PITCH_P / ROLL_P | 8 (now) | -9 | rate PM 79 @3.4 Hz, att PM 69 @1.25 Hz |
| att P | 5 / 4.5 / 4 | 27 / 47 / 71 | att fc 0.79 / 0.71 / 0.63 Hz, PM 77 / 78 / 79; rate loop unchanged |
| rate K_P | 20 -> 8 | -14 (no help) | rate fc 3.4 -> 1.3 Hz |
| ACT_TC | 0.033 -> 0.005 | -46 (no help) | rate PM 79 -> 59 |
| G1 default x0.5 (shifts e box to 0.25..1) | 0.5 | 50 | rate PM 50 @10 Hz, rate loop unstable at the fast corner (-121) |
Only attitude P restores >= 30 deg: about 4.7 (<= 5 gives 27, 4.5 gives 47); nominal cost: attitude crossover 1.25 -> ~0.7 Hz, PM
slightly up (69 -> 78). With the slow value to 9x the box stays unstable down to P 2.5 (P 2: 19 deg at e 2, tau x9).

## Model limits (unverified)
- Rotor tau 33 ms nominal is assumed; asymmetric up/down enters as one linear tau (slow = bound, mean = typical); true behaviour is nonlinear
  and between the two, run 7 and 13 are the sensitive ones.
- Not modelled: eta x motor state on the measured path, eRPM dropout (run 17: 20 %), vibration, weak motor / sag, yaw, outer position loops.
- Delay glue: act+imu loop delay is lumped into command latency, telemetry frames assumed 1.25 ms each on the measured path.
- Run 19 roll predicted PM 2 deg (slow) but no oscillation reported: not checked in the log. Run 17 roll (PM 23 slow) quiet in the log.
- The 1.8 Hz limit cycle amplitude (saturates at 35 deg) is nonlinear; the model only says the linear loop is at or past the stability edge.
- PM from `margins_est.margins` on a 500-point grid (coarser than `margins_of`; self-test checks the helper and a known PM 61.35 deg).
