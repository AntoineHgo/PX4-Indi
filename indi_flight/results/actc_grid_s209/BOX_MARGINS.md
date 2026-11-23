# Linear margins at the proposed G3 ACT_TC box corners (S209, model only, no flight)
Run from the repo root (~2 min): `python3 -I indi_flight/results/actc_grid_s209/box_margins.py 800 400 > indi_flight/results/actc_grid_s209/box_margins.tsv`
Per-cell output in `box_margins.tsv`. Method = `q26_kscale.py` / MARGINS_S200: `margins_s200.cfg/loops`
(bench `margins_models.L_indi`, `margins_est.margins`, flown freeze config, measured path, Tb 1 s, MC_ROLL/PITCH_P 8, pitch, K 20).
The model takes one plant tau_r: asym 1 = tau_mean; asym 3 brackets = tau_slow 1.5 m and tau_fast 0.5 m (m = tau_mean). Controller ACT_TC = r m,
r in {0.88, 1.0, 1.02}; fixed rule = 0.033 s. Lead c = min(K ACT_TC, 2). Each number is the worst over G1 error e {0.8, 1.2} x telemetry frames {0, 3}
(the realised-box corners of Q27; symmetric fixed 0.033 reproduces the Q27 5.7 deg); delay = added loop delay 0 or 10 ms. "rate" = rate loop alone, "rate+att" = M3a break, attitude path closed.

Worst PM deg / GM dB / DM ms over r and the three plant variants (asym 1, slow, fast), 800 Hz:
| plant m x0.033, delay | box rate | fixed rate | box rate+att | fixed rate+att |
|---|---|---|---|---|
| 0.5, 0 ms | 67/11.3/44 | 79/8.5/21 | 39/11.2/38 | 54/8.3/21 |
| 0.5, 10 | 57/5.2/35 | 42/2.3/11 | 28/5.1/27 | 42/2.2/11 |
| 1, 0 | 64/10.8/28 | 66/10.9/29 | 32/10.5/28 | 35/10.6/29 |
| 1, 10 | 52/4.1/19 | 53/4.2/19 | 23/4.0/19 | 25/4.0/19 |
| 3, 0 | 60/10.5/20 | 41/17.2/50 | 28/10.2/20 | 1/16.9/2 |
| 3, 10 | 31/3.4/10 | 34/9.6/40 | 20/3.2/10 | -6/-26.2/-8 (unstable) |

Overall worst (all cells):
| | PM | GM | DM |
|---|---|---|---|
| box, rate, 800 Hz | 30.6 (m 3, fast, 10 ms, r 1.02, e .8, fr 0) | 3.4 (m 3, fast, 10 ms, r 1.0) | 10.4 (same corner as PM) |
| box, rate+att, 800 | 19.9 (m 3, slow, 10 ms, r 0.88, e 1.2) | 3.2 (m 3, fast, 10 ms, r 1.0) | 9.6 (m 3, fast, 10 ms, r 1.02) |
| fixed, rate, 800 | 34.5 (m 3, slow, 10 ms) | 2.3 (m 0.5, fast, 10 ms) | 10.9 (m 0.5, fast, 10 ms) |
| fixed, rate+att, 800 | -5.5 (m 3, slow, 10 ms, e 1.2, fr 3) | -26.2 (m 3, slow, 10 ms) | -8.3 (same) |
Symmetric plants only (asym 1): box rate 53/6.9/32, rate+att 32/6.7/26; fixed rate 43/4.2/19, rate+att 5.7/4.0/7.5.
400 Hz: same ordering. Box worst rate 29/2.8/9.9, rate+att 18.7/2.9/9.5; fixed rate 27/0.7/5.1, rate+att -6.8/-19/-10.5.

Reading. The box removes the fixed rule's instability at slow motors (m 3, 10 ms) and lifts the symmetric worst rate+att PM from 5.7 to 32 deg.
Box worst PM: slow-end asymmetric motor (tau_slow 149 ms), r 0.88 (19.9 deg; r 1.0 gives 24.2, r 1.02 24.5): under-estimating tau costs ~4.6 deg there.
Box worst GM 3.2 dB: fast-end asymmetric m 3 (tau 50 ms) with 10 ms. Asym 3 costs ~12 deg PM vs symmetric. The fixed rule is better only on fast motors (m 0.5, 0 ms: 54 vs 39 deg PM).
Not modelled: one first-order lag for the plant (up/down asymmetry represented only by the slow/fast brackets, not the nonlinear switching);
measured path = eta x motor state with eta 1 (no fault); pitch only (yaw structure, L_indi_yaw, not run); attitude loop only as the rate+att
break (stock P, no outer position loop; att-loop margins not computed here); no saturation, rate limit or injector; single added delay
and telemetry frames as lumped samples; controller bias beyond r (G1 error only e 0.8/1.2); identification noise of tau_sym_hat.
