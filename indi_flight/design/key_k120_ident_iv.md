# Second key k120: ident_iv.py (2SLS G1 estimator)

Evidence: `indi_flight/bench/tests/test_ident_iv_k120.py` (own plant: alpha = G1 u_act + c0 + OU disturbance,
u_act = 30 ms lag of command, command = -K*filtered rate + multisine z, 800 Hz, 60 s, G1 = 80; own numpy 2SLS written
before reading ident_iv.py). Run in Docker, 4 GB cap: 16 pass, 4 fail (failures = findings below, not flakiness).
Not run: real flight data, ulg path (`audit`), `prepare_regression` with a mismatch (only the raw iv call was mismatched).

## Verdict per function
- `iv_effectiveness` point estimate: AGREES with reference (beta, intercept, se, F identical to 1e-9 for 4, 12 and 14
  lags). Closed loop: IV rel. error -1 %..+1 %, OLS -55..-59 % (OLS bias real, IV unbiased). Intercept 5.82 vs true 6.0.
- `iv_effectiveness` uncertainty: DEFECT (se over-confident, see M1). Rank handling: DEFECT (M2). No mismatch check: DEFECT (B1).
- `prepare_regression` / `apply_taps` / `smooth_taps`: AGREE on reading. y and x and z use the same taps and the same
  `mode="same"` (zero phase), `np.gradient` adds no delay. Only a code-path guarantee, the estimator cannot verify it (B1).
- `latency_by_xcorr`: not re-derived (test_d/d2 of the existing file pass); UNVERIFIED by me.
- Memory: AGREES. n=50 000, 14 lags: tracemalloc peak 86 MB (O(n q)), no n x n array (ident_iv.py:149-154).

## Findings
- BLOCKING B1 (spec iii): ident_iv.py:113-170 has no consistency check between regressor and regressand. Self-test with
  a mismatched filter (y fc 40 Hz, x fc 15 Hz) returns beta/G1-1 = +0.74, +0.82, +0.97 with F = 66-70 and se/G1 = 3 %:
  confidently wrong, not rejected. A 4-sample (5 ms) delay of x gives -7 %, -9 %, -5 % with F ~ 200, se 0.8 %: silently
  biased. It "fails" only in the sense that the number is wrong; the estimator never flags it. Fix: over-identification
  (Hansen J, HAC) test in the result, see patch. Measured on my plant, lags 0..24, HAC window 150: correct data
  J = 4..16; delay mismatch J = 179..198; filter mismatch J = 158..185 (df 6). Chi2 calibration of J not verified.
- MAJOR M1 (spec ii): ident_iv.py:159-161 se is classical `s2 (Xh'Xh)^-1`, residual is serially correlated (coloured
  disturbance, tau 0.1-0.2 s) so se is too small. z-score std of (beta-G1)/se over 20 seeds: 1.69 on my plant,
  2.70 on the test_c plant (calibrated = 1). With Newey-West/HAC (window 100-300 samples at 500 Hz) it is 1.15-1.19.
  F (ident_iv.py:162-169) has the same flaw but only inflates; weak-instrument detection still works (below).
- MAJOR M2: ident_iv.py:151 `np.linalg.pinv(Zf)` with default rcond. 14 tones span only 28 dims and lagged sinusoids are
  nearly collinear: with 25 dense lags ident beta 78.20, F 274 vs lstsq reference 77.65, F 257 (0.7 % / 7 %); noise
  directions are fit and the dof q is overstated. Not triggered by the default 4 lags (agrees to 1e-12). Fix: rcond=1e-10 and use rank in F dof.
- MINOR m1: ident_iv.py:135 default lags 0..3 (6 ms at 500 Hz) is only a 4-column, highly collinear instrument set; more
  lags spanning the loop dynamics did not help much on test_c (sd 0.114 -> 0.092) so it is not the cause there.
- MINOR m2: docstring :122 says z is "uncorrelated with the disturbance by construction"; true only if the injector
  is not itself driven by feedback. Nothing checks it. Measured corr(z, d) = 0.003 in test_c plant (fine).
- MINOR m3: `exclude` after lagging (ok) but filter-support dilation of saturation is only in prepare_regression; a caller
  using iv_effectiveness directly gets no dilation. Documented, unchanged.

## test_c_intercept diagnosis (tests/test_ident_iv.py:81-85): verdict (c), finite-sample variance
Plant: closed_loop(0.5, seed, c0=12), 120 s. 20 seeds, default lags: mean bias of beta/G1-1 = +0.030, sd across seeds
0.114, so mean/sd = 0.26 sigma (not significant); 12 of 20 seeds exceed the 0.05 threshold; seed 11 gives +0.077 (0.67 sd).
Intercept mean 12.45, sd 1.64 (truth 12: ok). Instruments are not correlated with d (corr 0.003-0.004), F median 222,
OLS bias -0.84, so identification is sound. Variance falls with record length: 240 s gives sd 0.043 (3/8 over 0.05),
240 s with 30 spread lags sd 0.032 (1/8). Roughly 1/sqrt(T), as expected with a 0.2 s disturbance (about 300 independent
samples in 120 s). It is not an estimator bug (a) beyond the over-confident se (M1) which hides the spread: reported
se/G1 = 0.037 vs true 0.114. It is a weak test (b): a 5 % threshold with 11 % sd is a seed lottery, and the test passes or
fails on the seed. Not loosened. Options for the owner: use >= 480 s or 5 seeds with a mean check, or assert |beta-G1| < 2.5 se_HAC.

## Weak instrument (spec ii)
My plant, z std 0.3 vs 1e-4: F 193 -> 1.2, beta 26.5 (truth 80), se 5.2 (units rad/s2 per unit, se/G1 6 %: classical se
does not warn, F does). So F is the usable gate (suggest F < 10 -> reject). Per-axis F and se are returned (spec ii met
for F; se needs M1).

## Proposed patch (ident_iv.py, not applied; scratch verified numerically, copy at /tmp/k120_patch.py)
```diff
-    Zf_pinv = np.linalg.pinv(Zf)  # (q+1, n)
+    Zf_pinv = np.linalg.pinv(Zf, rcond=1e-10)  # (q+1, n); M2
...
-def iv_effectiveness(y, x, z, lags=None, exclude=None):
+def _hac(U, L):  # O(n q) memory
+    S = U.T @ U
+    for l in range(1, L + 1):
+        G = U[l:].T @ U[:-l]
+        S += (1 - l / (L + 1)) * (G + G.T)
+    return S
+
+def iv_effectiveness(y, x, z, lags=None, exclude=None, hac_lags=200):
...
-    cov = s2 * np.linalg.inv(Xh.T @ Xh)
+    A = np.linalg.inv(Xh.T @ Xh)
+    cov = A @ _hac(Xh * res[:, None], hac_lags) @ A            # M1 (keep classical as se_classical)
...
+    g = Zf * res[:, None]; S = _hac(g, hac_lags)                # B1: Hansen J on excluded instruments
+    gm = g.sum(0); J = float(gm @ np.linalg.pinv(S, rcond=1e-10) @ gm)
+    df = int(np.linalg.matrix_rank(S, tol=1e-10 * np.linalg.norm(S, 2))) - (k + 1)
+    out["j_stat"], out["j_df"] = J, df     # caller rejects when J > chi2_{0.999}(df) or f_min < 10
```
Note: hac_lags must be given in samples for the caller's rate (about 0.5 s). The J threshold needs a recheck with real data.

## S120 resolution (orchestrator)
Applied: B1 (Hansen J, HAC-weighted, returned as j_stat/j_df), M1 (HAC se, Bartlett, hac_lags=200 samples; classical
kept as se_classical), M2 (pinv rcond=1e-10). test_c_intercept rewritten as a 12-seed test: intercept mean within 1.0,
beta mean bias within 3 SEM (single-seed 5 % was a seed lottery; absolute 10 % accuracy is D-IDENT acceptance (i), in
flight), HAC z-spread in (0.5, 1.6). K120 tests updated to assert the fixed behaviour (J aligned 5-20 vs mismatched
147-178). 20/20 pass in Docker. Mutations caught: J forced to 0 (flagged test fails), hac_lags=0 (test_c fails).
Open, not blocking the next step: latency_by_xcorr not re-derived (key it with the flight data); mismatch through the
prepare_regression path untested; J rejection threshold to calibrate on SITL flight data (chi2_0.999(3)=16.3 is below
aligned J=20 here); HAC treats rows dropped by `exclude` as contiguous.
