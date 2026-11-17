# T128 G2-STEP primary metric script (S63)

Built `bench/g2_step_metrics.py` (CLI: `OUT.json FLIGHT_DIR...`, JSON list + markdown table) and
`bench/tests/test_g2_step_metrics.py` (7 pytest tests, synthetic arrays, no ULog). Written to the GATES.md G2-STEP
"Measurement definition (S63)" only; the independent second key was not opened.

## Tests
`python3 -m pytest -q bench/tests/test_g2_step_metrics.py` -> 7 passed. Host pytest is broken by the xonsh plugin
(and not installed): ran from a scratch venv with `-p no:xonsh`.
Cases: zeta 0.5 second order (OS 16.3 %, settle vs dense brute force), first order tau 0.1 (OS 0, settle 391 ms,
rise 220 ms), negative step == positive, return step excluded (glitch 40 ms before return, window 2950 ms),
truth = est - ramp (pre 0, end 0.22 deg), never settles -> NaN (and ringing -> last-violation time), yaw 45 deg.
Break-check: (1) window end = t_next (no 50 ms margin) -> test_return_step_inside_window_is_excluded FAILED;
(2) window dropped (to end of data) -> failed too; restored, 7 passed.

## 9 flights (results/stage3_s63/g2_step_primary_s62.json)
All 9 pass. est OS 0.25-0.97 %; roll/pitch settle 339-371 ms, rise ~208-211 ms; yaw settle 899-914 ms, rise 540-550 ms;
truth OS <= 0.85 %. Matches the expected ranges, no tuning of the script. est-truth: pre ~0 (yaw +0.5..0.7 deg),
end roll/pitch +0.21..0.24 deg, yaw +0.62..0.91 deg (agrees with the A-28 note). Truth settle (reported only) is
NaN or ~2.9 s in two cases (seed2 yaw, seed3 roll): est-truth bias is near the 2 % band (0.3 deg roll, 0.9 deg yaw).

## Ambiguities resolved
- First step only (after t_window_start_us); later step pairs ignored. No return step found -> window to end of data.
- Crossing threshold: 50 % of the NOMINAL amplitude (15/45 deg) for t_on; then step = median(sp, [t_on, t_on+1 s)) - pre
  median; t_next search uses 50 % of the measured step, starts at t_on + 1 s (earlier, the 1 s median still holds the
  old level). So a hold shorter than 1 s is not supported (scenarios hold 3/4 s).
- Reference for est/truth: pre-step setpoint median + step (setpoint final), angles normalised so the step is positive;
  wrapped to +-180 (yaw). Overshoot = max(0, peak - step)/step. Truth interpolated on estimate timestamps.
- Settle = time of the first in-band sample after the last out-of-band sample, from t_on; NaN if the last window
  sample is out of band. Rise = linear-interpolated first crossings of 10 % and 90 %. t_on is a setpoint timestamp.
- Est-truth reported in raw physical sign (not step-normalised); end mean over [t_end-1.5 s, t_end).
- pass = est OS, est settle (non-NaN) and truth OS all within limits; truth settle is not in it.

## Second-key comparison (orchestrator, S63)
Against `results/stage3_s63/t127_key_g2_s62.md` (T127 key, est_g2/gt_g2, written independently): est overshoot equal to
0.01 % on 9/9 flights, est settle equal to one sample (1.25 ms) on 9/9, rise within 2.5 ms (sample vs interpolated crossing),
truth overshoot equal, truth settle equal except seed1 pitch 371.25 vs 368.8 ms (reported metric). Window end differs by
<= 10 ms on 2 flights (return-crossing detection), no metric affected. Verdict AGREE: the primary is usable for the first
G2-STEP test. Host has no pytest: tests run from a scratch venv with `-p no:xonsh`.
