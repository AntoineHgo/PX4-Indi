# K125: second-key review of the K124 fix (S124), bench/ident_fit.py + bench/tests/test_ident_fit.py

Scope: findings 1-3 (BLOCKING), 5-6 (MAJOR) of design/key_k124_ident_fit.md versus fix_k124_s124.md.
Mutations on copies in /tmp/k125 (repo untouched; `git diff --stat indi_flight/bench` empty). Baseline: 10/10 tests pass (~170 s total).
NOT verified: real-log numbers (no ulogs run), Docker/SITL, ident_iv.py internals beyond j_df.

## Verdict table
| K124 finding | status | evidence |
|---|---|---|
| 1 BLOCKING no failing mismatch self-test | PARTIAL | Shift mismatch: FIXED. ident_fit.py:30 bound, :170 at_boundary, :192 criterion; test_mismatch_shift_beyond_scan_bound_fails; mutation at_boundary=False -> test FAILS. Filter mismatch: test exists and fails when chain criterion is neutered (M1: chain_mismatch->0 => test FAILS, so it really depends on that criterion). But the criterion is computed from the ntaps ARGUMENTS (ident_fit.py:172, chain_mismatch:75-87), not from the data path. Mutation M2 (drop C=[1,4,1]/6 from x and z in _prepare:136-137): ALL tests pass, including test_regressand_regressor_same_gain_at_60hz (checks only the constant) and the clean-run gate. So the real chain can silently diverge from the gated chain. Also: a pure delay inside the scan range is still absorbed (by design, documented). |
| 2 BLOCKING no gate | PARTIAL | Verdict dict and exit code exist (ident_fit.py:181-195, main :237). F, shift-boundary, CI, excl, chain are real gates. The J gate is not: J/df <= 20 (GATE:32) accepts every real log (14.7-15.0) and the mismatches (12.9-14.6); fix doc admits it (threshold set ~1.35x the real logs). No p-value. compensate_latency=False makes at_boundary always False (:170). |
| 3 BLOCKING classical F | PARTIAL | robust_first_stage_f (:48-76), MOP effective F with HAC, computed on the final shifted, decimated, excluded stage (:140-141, same lg, hl). Unit test known-answer is meaningful (hac lags 0 breaks it per fix doc; I did not re-run that). But driver wiring is untested: M3 (driver gate uses classical f_first instead of robust) -> all tests pass, including weak-instrument and clean-run. Also the MOP "effective F >= 10" threshold is not the MOP critical value (tau-dependent; 10 is the 2SLS rule of thumb); acceptable as stated, label it as such. |
| 5 MAJOR shift scan unbounded / one chain | FIXED (scan) / PARTIAL (chain) | Scan bound -2..12 (:30) and boundary FAIL, integer shifts, shift applied after filtering (_lead :90-99). Chain: see 1 (design correct, enforcement tautological). Scan J uses 80 HAC lags, final 400 (:156 vs docstring at :154 "same HAC lags in scan and final fit": docstring false, fix doc admits deviation). |
| 6 MAJOR held (ZOH) regressor | FIXED | update_rate (:37-45) refuses < 25 % changing samples, HeldRegressorError caught in main (:231). Changed-sample interpolation + decimation m (:131-133, :140), lags/hac scaled (:138-139). Test covers hold 8 refused, hold 2 decimated, G1 within 8 %. Caveats: update_rate runs on the whole log u, not the window; a log with intermittent holds inside the window is not caught; no test that decimation m=1 mutation fails (fix doc claims it was checked, not re-run). |

## New defects / weaknesses introduced
1. (MAJOR) Chain-gain criterion is tautological for the code path: it depends only on (ntaps, ntaps_x) and a hard-coded C. Fails only via the test hook. See M2. Fix: compute the gain from the arrays actually used (e.g. filter an impulse/sinusoid through the same functions used in _prepare for both sides), or add a test that runs _prepare on a 60 Hz sine and compares x-chain vs y-chain amplitudes.
2. (MAJOR) J gate threshold tuned to pass real logs (20 vs 14.8; null synthetic 7.4). J/df ~ 2x the null means the Hansen J is not testing anything: reported as a gate in the verdict table, it will never fail on real data. Label it informational or drop it from `passed`. Also j_df = rank(S) - 2 (ident_iv.py:185) is the NUMERICAL rank of the moment covariance (df 7 observed for 17 lags), so J does not have a chi2(df) reference and J/df is not interpretable as a ratio of a chi2 mean. Cause of J~103 still open (the fix doc says so).
3. (MINOR) Held-regressor and clean-run gate tests pass but the weak-instrument test would also pass with the classical F (M3): the test does not discriminate the F estimator.
4. (MINOR) Test mismatch (b) is only caught by one criterion; G1 -46 % with unchanged J and F. Acceptable, but means chain gate is the single guard (see 1).
5. (MINOR) compensate_latency=False disables the boundary gate silently.
6. (MINOR) Docstring fit_axis :154 stale ("same HAC lags").

## Remaining open (K124 MAJOR 7-9, MINORs)
- MAJOR 7 saturation mask coarse (convolve over len(taps), _prepare:144-146; nothing new): MAJOR, unchanged.
- MAJOR 8 self-test realism (integer delay only, no actuator lag, single seed 3): MAJOR-minus; only seed 3 used for all gate tests, thresholds untested for robustness.
- MAJOR 9 CI conditional on chosen shift; first-stage lags 0..32 only: MODERATE; CI +-2 % on a shift picked by min J is optimistic.
- MINOR fs hard-coded in load/CLI (no --fs), intercept/axis-order assertion, stale header pieces, no ulog load test: MINOR each; ulog loader (:204-218) untested is the most relevant (wrong axis or timestamp would not be seen).

## Overall verdict: fix usable for D-IDENT evidence: YES with caveats
The decisive pieces (verdict + exit code, robust F on the right stage, bounded shift with boundary FAIL, held-regressor refusal) are real and exercised by failing tests. Caveats to record with the evidence: (a) the J gate carries no discriminating power on real logs, evidence must not cite "J passed"; (b) the chain-match gate checks parameters, not the data path (M2), so condition (iii) is by construction plus review, not by test; (c) F wiring in the driver is untested (M3). Recommend two cheap tests (sine through _prepare; driver f equals robust f) before citing condition (iii) as test-enforced.
