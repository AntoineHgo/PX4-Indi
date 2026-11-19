# K126 second key: ident_fit_yaw.py vs "Model and firmware convention" / "Self-test" of fit_yaw_s125.md

Reviewed: indi_flight/bench/ident_fit_yaw.py (246 lines), tests/test_ident_fit_yaw.py, helpers in ident_fit.py / ident_iv.py
(`_lead`, `update_rate`, `chain_mismatch`, `load`, `_hac`, `_shift`, `resample_to_grid`, `apply_taps`). Results and Reading sections of the
spec were not read. Static review plus running the self-test and one mutant.

## 1. IV maths
- 2SLS (ident_fit_yaw.py:84-89): beta = (Xh'Xf)^-1 Xh'y with Xh = P_Z Xf, intercept in both X and Z. Correct.
- HAC covariance (:91-92): A (Xh' res-weighted HAC) A with A=(Xh'Xh)^-1, Bartlett kernel, rows Xh*res. Correct sandwich for 2SLS. CI = 1.96 se (:166,169), normal, no weak-IV-robust alternative (acknowledged in the spec).
- Hansen J (:93-97): J = gm' S^+ gm with gm = sum of Zf*res and S the unnormalised HAC. Scale is consistent. BUT the residuals are the 2SLS ones, not the two-step efficient GMM ones, so J is not asymptotically chi2(df); it is stochastically larger. df = rank(S) - 3 uses a numerical rank of a nearly collinear instrument set (17 + 9 lags of band-limited signals plus constant), so df is set by the 1e-10 tolerance, and the pinv(S, rcond=1e-10) inverts directions that are numerically noise. J/df <= 20 is lenient enough that this is mostly harmless, but J/df is not a calibrated over-identification test. See MAJOR-1.
- df can be <= 0 (rank collapse): `jr = j / max(df,1)` (:171) then gates J alone; no gate requires df >= 1. See MAJOR-2.
- SW conditional F (:100-116): x_j~ = x_j - Xhat_{-j} gamma, gamma from OLS of x_j on [1, Xhat_{-j}], then F of x_j~ on Zf with numerator df q-(k-1), denominator n-q-1. This is the standard SW construction. Classical F correct. HAC effective F (_eff_f, :58-68): pi'Gc pi / tr(Gc V_zz) with Gc the Schur complement. Reduces to the classical F under homoskedastic white errors (checked algebraically). Correct in form. Caveats: MOP's 10 critical value is derived for one endogenous regressor; with k=2 and 26 near-collinear instruments the F_eff >= 10 threshold has no formal meaning (MINOR-3).
- Filters: y = F[D w], x1 = F[C u], x2 = F[D u], z1 = F[C d], z2 = F[D d] (:38-48), same 15-tap F everywhere, D = np.gradient (gain sinc) on y and x2, C = [1 4 1]/6 on x1 and z1 (gain-matched to D). Consistent in the middle of the band. Note: the x2 chain is not covered by the `chain_mismatch` gate (it compares only the G1 column and only checks ntaps vs ntaps, which is identically 0 in production, :170). See MINOR-2.
- Intercept: handled as regressor and instrument; reported (`intercept`). OK.

## 2. Time base
- Everything is placed on one 800 Hz grid t_grid (:35). Gyro and d go through `resample_to_grid`, which refuses sources slower than the grid (loud ValueError); good, no ZOH of the gyro or of d.
- Regressors: u is decimated (update period m = 2 according to the spec). `xg` is a LINEAR interpolation between true updates (:41-43), not a ZOH (good), but linear interpolation of a 400 Hz sampled signal low-passes with gain sinc^2(pi f / 400): 0.984 at 20 Hz, 0.93 at 60 Hz. y and the instruments (genuine 800 Hz) do not have this loss, so x1 and x2 are attenuated relative to y/z in the upper band, and the chain gate cannot see it (it models only C and F). Effect: G1 and G2 biased high by the (spectrum-weighted) loss, roughly 1-3 percent for a 1-60 Hz multisine. Estimated analytically, not run on data. See MAJOR-3.
- Latency shift (:150-153): `_lead2` leads the regressors by k and the instruments and y stay put. Instruments are exogenous lagged d, so shifting only the regressors is the right choice (shifting y would only move the sample window). Shift is applied to x1 and x2 jointly (spec: common). OK. The rows that become NaN at the ends differ with k, so J across k is computed on slightly different n (<= 14 of ~21000 rows): negligible.
- The saturation exclusion `excl` is not shifted with the regressors (:153, :157): rows excluded in y-time while the regressor row is at t+k. Offset <= 12 samples against a 15-tap padding already included: negligible (MINOR-4).
- Timestamps: load() uses `timestamp_sample` for gyro, u and inject (ident_fit.py:232-233), but `timestamp` (publish time) for control_allocator_status (`t_sat`, ident_fit.py:236). Used only for the saturation mask, so the mixing is harmless at the level of the 15-tap padding. A missing `timestamp_sample` in indi_rate_status would raise KeyError (loud). OK.
- `with_g2=False` path: `excl_frac=0.0` is hard coded in `_fit1` (:208), so the excluded-fraction gate trivially passes in the --g1-only contrast. That path is documented as contrast only (MINOR-5).

## 3. Sign / units of G2
- Model alpha = G1 u + G2 du/dt, du/dt via np.gradient(xg, dt) with dt = 1/800 s, so du/dt is per second and G2 has units rad/s. This agrees with the firmware backward-Euler form (G1 + G2 s) Delta cited in the spec (indi_rate_control.cpp:456-459: g2/dt * (inc - prev_inc)) and with the plant model of the firmware unit test. G2 > 0 adds with G1. No sign flip anywhere in the script. Not independently re-read in the firmware source (spec lines only), flagged unverified.
- The fit uses measured u where the firmware term acts on the commanded increment; the spec acknowledges this. With a latency scan applied to both regressors, d(u)/dt shift and u shift are forced to be equal, which is the correct physical constraint.

## 4. Gates
Implemented as in the spec: F_eff >= 10 per regressor, J/df <= 20, interior shift, CI/G1 <= 0.15, CI/G2 <= 0.5, chain, excluded fraction (:174-187).
- NaN safety: every gate is `value <= / >= threshold`; NaN compares False, so NaN fails. Good (`passed = all(...)`, :188). The F_eff gate could not pass silently on NaN.
- Silent-pass paths: (a) df <= 0 (MAJOR-2); (b) `chain_mismatch(ntaps, ntaps)` is a pure formula check independent of data and cannot fail with the default 15 taps; `chain_mismatch_measured` exists in ident_fit.py:109 but is not used (MINOR-2); (c) g1-only `excl_frac` constant (MINOR-5); (d) `at_boundary` only tests the J-minimum on the scan edge (:164) and `np.argmin` of a curve containing NaN returns the NaN index, silently selecting a bogus shift (MINOR-6); (e) no minimum n or window coverage gate: an empty window raises (loud), a very short one passes if CIs happen to be small.
- CI/|G2| is inf when G2 = 0: fails (correct), but a legitimate G2 ~ 0 plant (test 3 situation) can never pass the gate (MINOR-7, by design, but the verdict should say "G2 not distinguishable from 0").

## 5. Self-test
- Known answer with BOTH regressors: yes (plant alpha = g1 u + g2 du/dt + dist, G1=200, G2=27, three loop gains), asserts G1 within 5 % or 1.5 CI and G2 within 8 %.
- Closed loop: yes (u_cmd = -kr w/g1_set + d, disturbance reaches u through w).
- Gate must FAIL: yes, test 4 (filter mismatch 7 vs 15 taps) asserts verdict not passed. It asserts only that SOME gate fails and prints which; it does not assert which one, and the hook adds its own extra chain gate (:184-187) so that test exercises the hook, not the production gates. No test makes the F_eff, J/df, boundary-shift or CI/G2 gates fail by themselves (weak instruments, excitation off, delay outside the scan range are all untested). See MAJOR-4.
- Not covered: decimated regressor (u at 800 Hz here, so m = 1 and the interpolation/decimation/`_build_Z` rounding branch is never executed; MAJOR-3/MAJOR-4); non-zero intercept; saturation mask; the latency shift value is never asserted (delay=2 samples is injected but `shift_samples == 2` is not checked); G2 sign negative.
- Run result and mutant: see section 6.

## 6. Mutation test
Unmodified self-test (ulimit -v 4000000): all 4 tests ok, 244 s wall time (slow for a unit test); test 4 reported failing gates
['CI/|G2|', 'chain FIR 7 vs 15'] with G1 1961, G2 0.09, J/df 13 (so J/df <= 20 and F_eff did not catch the mismatch on their own).
Mutant (copy in /tmp/mut, regressor latency shift removed: `Xs = X[sl]` instead of `_lead2(X,k)[sl]`, test pointed at the copy):
test_recovers FAILS at the first case, G1 = -680 vs 200 (assertion on G1). So the shift (and G1/G2 together) is protected. The repository
script is untouched (git status shows only the pre-existing STATE.md change).

## Findings

BLOCKING
- none found by static review (2SLS, HAC, SW F and sign/units match the specification).

MAJOR
- MAJOR-1 ident_fit_yaw.py:93-97 J uses 2SLS residuals with an HAC weight and a numerical-rank df on collinear lags: not chi2(df). Fix: compute two-step efficient GMM residuals for J (or label J/df as a diagnostic and calibrate the 20 on simulation), and report df from rank(Zf)-3.
- MAJOR-2 ident_fit_yaw.py:171,176 `max(df,1)` lets df <= 0 pass the J gate. Fix: add a gate `j_df >= 1` (fail otherwise).
- MAJOR-3 ident_fit_yaw.py:41-45 regressors come from linear interpolation of a 400 Hz topic (gain sinc^2) while y and instruments are native 800 Hz: ~1-7 percent gain loss across 20-60 Hz, uncovered by the chain gate, biasing G1/G2 high; the self-test never exercises m = 2. Fix: either fit on the decimated grid (decimate y and z with the same antialias path) or add the interpolation gain to the chain model and add a decimated-u synthetic test.
- MAJOR-4 tests/test_ident_fit_yaw.py:67-72 and whole file: no test makes a production gate fail on its own (F_eff, J, shift boundary, CI/G2), and shift value is not asserted. Fix: add tests for weak instruments (d amplitude ~0), delay outside scan range (boundary flag), assert `shift_samples == delay`, and assert the failing gate name in test 4.

MINOR
- MINOR-2 ident_fit_yaw.py:170 `chain_mismatch(ntaps, ntaps)` is data independent, x2 chain never gated. Fix: use chain_mismatch_measured on the actual x1/x2 chains.
- MINOR-3 ident_fit_yaw.py:174 F >= 10 threshold is a single-regressor MOP rule of thumb; with k = 2, q = 26 it is a heuristic. Fix: document, or compare to the SW F with Stock-Yogo critical values for K=26.
- MINOR-4 ident_fit_yaw.py:153 excl mask not shifted with the regressor lead. Fix: shift excl by k.
- MINOR-5 ident_fit_yaw.py:208 hard-coded excl_frac=0.0 in `_fit1`. Fix: compute the same excl fraction.
- MINOR-6 ident_fit_yaw.py:161 `np.argmin(jv)` returns a NaN index if any J is NaN. Fix: `np.nanargmin` plus fail if any NaN, or require all finite.
- MINOR-7 ident_fit_yaw.py:180 CI/|G2| gate has no meaningful outcome when G2 ~ 0. Fix: report "G2 consistent with 0" separately from gate failure.

Unverified: firmware source lines (cpp:456-459) not re-read; real-data behaviour not run; MAJOR-3 magnitude derived analytically.
