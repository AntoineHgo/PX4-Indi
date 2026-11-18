# S84 HF output break z: second key (independent recomputation)

## Method
Input: hf_pinj_z.csv (t,d,x=u=t_c_applied,y=c=t_c), 3556 samples, 40 s = 8 periods of 5 s, fs 88.9 Hz, time base
non-uniform (margins_est uses its least-squares phasor path). First period dropped, 7 periods averaged, 9 excited bins
(log_bins 1.5-10 Hz). L = -G_yd/G_xd (pinj_csv convention). Two computations:
(a) bench/margins_est.frf_periodic on the raw CSV; (b) my own per-period LS phasor fit with a constant term, H1 averages
over periods, same sign convention. (c) (a) again with x,y mean-removed. Coherence = min(g2_xd, g2_yd) for (a)/(c).
Scratch scripts were not kept in the repo (in the session scratchpad).

## Result (b) = (c), 7 periods; coherence min(g2x,g2y); all bins >= 0.98, none unusable
| f Hz | |L| dB | arg L deg | coh | first key dB / deg | diff dB / deg |
|---|---|---|---|---|---|
| 1.6 | -10.09 | -124.0 | 0.999 | -10.1 / -124.0 | 0.0 / 0.0 |
| 1.8 | -11.83 | -124.9 | 0.997 | -11.8 / -124.9 | 0.0 / 0.0 |
| 2.4 | -16.36 | -123.0 | 0.990 | -16.4 / -123.0 | 0.0 / 0.0 |
| 3.0 | -20.93 | -112.0 | 0.990 | -20.9 / -112.1 | 0.0 / 0.1 |
| 3.8 | -22.88 | -82.8 | 0.988 | -22.9 / -82.8 | 0.0 / 0.0 |
| 4.8 | -20.75 | -62.1 | 0.985 | -20.7 / -62.1 | 0.05 / 0.0 |
| 6.0 | -18.62 | -75.2 | 0.993 | -18.6 / -75.2 | 0.0 / 0.0 |
| 7.6 | -17.31 | -100.7 | 0.995 | -17.3 / -100.8 | 0.0 / 0.1 |
| 9.4 | -17.80 | -131.0 | 0.997 | -17.8 / -131.2 | 0.0 / 0.2 |
Per-period scatter of L about the mean: 1-5 percent (relative), coherence from only 7 averages is optimistic but the scatter
confirms it.

## Verdict: AGREE
- |L| -10.1 dB at 1.6 Hz, -22.9 dB at 3.8 Hz, -17 to -18 dB over 7.6-9.4 Hz (-17.3, -17.8): AGREE.
- arg L -62 to -131 deg (min -62.1 at 4.8 Hz, max-lag -131.0 at 9.4 Hz; -125 at 1.6-1.8 Hz): AGREE.
- No -180 deg crossing in 1.6-9.4 Hz: AGREE at the 9 measured bins (lowest arg -131 deg at 9.4 Hz). Between bins and
  above 9.4 Hz nothing is measured; phase is falling at 9.4 Hz so a crossing just above the band is not excluded.
- GM > 17 dB in this band: AGREE, with the caveat that it is a lower bound inside the band only (|L| <= -10.1 dB
  everywhere; at the highest-lag bin |L| = -17.8 dB, so a -180 deg crossing above 10 Hz would give GM near or below
  ~18 dB if |L| stays flat; not measured).
- Claim's "-17 to -18 over 7.6-9.4" holds only at the two end bins; 6.0 Hz is -18.6 and 4.8 Hz -20.7 (no contradiction).

## Tool finding (NOT fixed, flagged): DC leakage in margins_est._ls_phasors
Run (a) on the raw CSV gives different numbers (e.g. 3.8 Hz: -25.0 dB / -42 deg vs -22.9 / -83) and g2_yd 0.07-0.79, so
ALL bins were rejected and margins_from_frf crashed (hf_margins.err). Cause: x and y have mean -9.80 and the LS design
matrix in _ls_phasors has cos/sin columns only, no constant, on a non-uniform time base where the tones are not exactly
orthogonal to DC. Removing the mean (run c) or adding a constant column (run b) reproduces the first key exactly.
So the crash in hf_margins.err was this, not (only) a missing crossover. Any CSV with a nonzero mean on the
non-uniform path is biased; suggested fix: add np.ones column to A in _ls_phasors (and re-run test_margins_est). I did not
change margins_est.py (out of the requested scope).

## Fix: pinj_csv.py --margins (no crossover / no accepted bins)
- estimate(): if fewer than 2 accepted bins, returns a margins dict with nan values and no_accepted_bins=True instead of
  raising IndexError.
- new crossing_report(res, mg): explicit gain/phase crossover status. --margins JSON now has "report". On this data
  (mean removed): "no 0 dB crossover in band (1.60-9.40 Hz, accepted bins), max |L| = -10.1 dB at 1.60 Hz" and "no -180 deg
  crossover in band, lowest unwrapped arg L = -131.0 deg at 9.40 Hz; |L| there -17.8 dB".
- Tests added to bench/tests/test_pinj_csv.py: test_no_crossover_reported_explicitly (K=0.3, |L| < 1 everywhere),
  test_no_accepted_bins_does_not_raise (the real crash path).
- Test evidence: before the fix the file run died with IndexError in margins() (and crossing_report did not exist), exit
  nonzero; after the fix `python3 -I bench/tests/test_pinj_csv.py` prints PASS for all 6 tests.
  Note the original crash trigger was the all-rejected path; the no-crossover path itself returned nan quietly in
  margins() but was not reported, now it is.

## Unverified
- Did not run the ulog-to-CSV step (used the supplied CSV); did not re-run the CLI end to end (--margins JSON checked
  through estimate/crossing_report on the CSV). margins_est tests not re-run (file untouched).
