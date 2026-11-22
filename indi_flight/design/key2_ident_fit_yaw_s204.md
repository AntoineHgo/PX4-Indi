# Key 2 (S204): bench/ident_fit_yaw.py @57e80feac8 and tests/test_ident_fit_yaw.py

**VERDICT: FAIL with 1 MAJOR** (code matches spec; the self-test cannot fail the "CI too wide" gate). 4 MINOR.
Method: read script/test/helpers, then 11 mutants in a scratchpad copy (bench/ untouched), single tests with timeout.
Not run: full suite, real-data fits, firmware source (cpp:442-459).

## K126 MAJOR 1-4 status
- K126-1 (J from 2SLS residuals): FIXED in code. _gmm_j (ident_fit_yaw.py:128-145) does step-1 W=pinv(HAC(Zf e1)), step-2 b2, e2, S2, J=gm' pinv(S2) gm with sums and long-run S (scale consistent), df=rank(Zf)-npar. Reported beta stays 2SLS (fine). Test power: see MINOR-1.
- K126-2 (df<1 passes): FIXED. Explicit gate "Hansen df >= 1" (:211); jr=inf if df<1 (:207). Test test_df_gate (lags1=[0],lags2=[0]) catches mutant M3.
- K126-3 (400 Hz u vs 800 Hz y): FIXED. _prepare2 (:30-63): gyro and z sampled at u's change stamps tc then np.interp; u interpolated through tc; rate regressor xr built from the same w. Mutants M5 and M11 (unmatched u / unmatched y+z) are caught by test_decimated_rate_intercept_closed_loop (G1 off by 25x).
- K126-4 (gates untested): PARTLY. Now covered: shift value (==2), both scan edges, weak-F by name, df, filter mismatch by name. NOT covered: CI too wide (MAJOR-1), production chain gate (MINOR-2).

## Math / construction checks (no defect found)
- Model: coefficient on xr is -Dr, reported dr = -bet (:204); M2 (sign flip) caught. du/dt via np.gradient(xg, dt): per second, G2 in rad/s. x1 uses C (gain-matched diff) on u, y uses D on w: chain consistent.
- Shift: base._lead(a,k): b[t]=a[t+k], applied to u columns only, rate column unshifted (correct, it is gyro). Scan on sl=::m, cand in samples; hs/hf = HAC lags//m. Off-by-one mutant M4 caught by shift test.
- No truth leakage: fit_yaw receives only measured w, u, injected z; truth g1/g2 appear only in tests. NaN safety: gates are value<=/>= so NaN fails; jfinite gate present. Edge: if ALL J are NaN np.nanargmin raises (loud, acceptable).
- Instrument z in the self-tests is the injected d, exogenous by construction; weak-IV test uses pure noise (F scale-invariant) so shrinking d is not what is tested; fine.

## Findings
- MAJOR-1 tests/test_ident_fit_yaw.py (no test) / ident_fit_yaw.py:215: gate "95% CI/|G1| <= 0.15" is never made to fail by any test; mutant M8 (gate forced True) survives every test I ran. In test_decimated the CI is ~0.0 (noise-free plant), so the gate is never even near its threshold. Spec requires CI-too-wide to fail by name. Fix: add a test with large noise or short window asserting "95% CI/|G1|" in failing gates (the weak-IV test fails it only as a side effect, and it asserts the F gate, not CI).
- MINOR-1 test_gmm_j_valid_vs_invalid_instrument (test:150-166): iid, homoskedastic data where 2SLS and 2-step GMM coincide, so reverting J to 2SLS residuals (M6) passes both that test and the decimated test. The two-step fix of K126-1 is therefore unproven by test. Fix: heteroskedastic/serially correlated DGP where 2SLS-J overshoots, or compare against a hand-computed e2.
- MINOR-2 ident_fit_yaw.py:206 chain_mismatch(ntaps, ntaps) is a pure formula (always 0 with equal taps) and cannot fail on data; the test only exercises the hook gate "regressor FIR 7 vs 15" (:221-224), not production. Carry-over of K126 MINOR-2; chain_mismatch_measured (ident_fit.py:109) still unused.
- MINOR-3 matched grid for the gyro-derived rate regressor alone is not discriminating: M10 (xr from raw 800 Hz gyro) passes (G1 204.8 vs 204.6, Dr 1.390 vs 1.387). Effect is small on this plant, but the test cannot prove xr matches; z-only raw not run.
- MINOR-4 test_decimated accepts shift in (-1,0,1) (test:125), so M4 off-by-one is invisible there; only the 800 Hz delay test pins the shift. Acceptable but note the decimated plant has no pinned latency.

## Break-check table (single tests, copy only)
| # | Defect | Test run | Result |
|---|---|---|---|
| M1 | drop rate regressor (cols) | decimated_rate | caught, but by accidental IndexError (f_eff list), not an assert |
| M2 | Dr sign flip | decimated_rate | caught (dr=-1.387) |
| M3 | df>=1 gate forced True | df_gate | caught |
| M4 | shift off-by-one (k+1) | shift_value_boundary / decimated | caught / SURVIVES (decimated) |
| M5 | u interpolated on t_u not tc | decimated_rate | caught (G1 5374) |
| M6 | J back to 2SLS residuals | gmm_j + decimated | SURVIVES |
| M7 | first-stage F gate forced True | weak_instrument | caught |
| M8 | CI/G1 gate forced True | decimated_rate | SURVIVES (no test targets it) |
| M9 | boundary tests only low edge | shift_value_boundary | caught (high-edge case) |
| M10 | xr from raw gyro | decimated_rate | SURVIVES |
| M11 | y and z from raw gyro/z | decimated_rate | caught (G1 5394) |
Baselines pass: shift 143 s, weak-F 35 s, df 1 s, gmm_j 0 s, decimated 36 s.
