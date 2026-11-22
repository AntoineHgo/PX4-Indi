# ident_fit_yaw.py fix (S202): r regressor + matched grid (probe V3), K126 MAJORs, A-44

STATUS: KEY 1 of 2 done, second key pending. Self-test (python3 bench/tests/test_ident_fit_yaw.py, pure host Python):
12/12 tests pass, 0 fail, 580 s CPU / 9m40 wall (selftest.log). Not committed.

## Known-answer results (recovered vs truth)
- G1 (closed-loop, g1_set 100/200/400): within 5 % of 200 or 1.5 CI, CI/G1 < 10 %, verdict passed (test_recovers).
- G2: within 8 % of 27 (test_recovers); m=2 decimated plant: 27.04 vs 27.0 (both seeds).
- G1, m=2 plant: 204.6 vs 205.3 truth (-0.3 %, asserted < 2 %). Dr: 1.387/1.388 vs 1.4 (asserted +-0.15).
- Delay: injected 2 samples recovered exactly (shift_samples == 2); m=2 plant within +-1 sample.
- Contrast: no du/dt term -> G1 biased > 10 %; no rate term -> G1 off > 10 % (A-43); mismatched filter chain -> G1 1939,
  caught by the CI and chain-gain-match gates.
- Only pass/fail asserts print numbers for the m=2 case; G1/G2 in test_recovers are asserted, not logged.

## Test fixes in this session (no tolerance loosened, no gate removed, fit code untouched)
- test_shift_value_and_boundary_gate: old case put the true delay (2) fully outside scan (5,12). J is then flat at noise
  level (~500) and the argmin is an arbitrary interior point (9), so no boundary gate can fire. Now the true delay sits
  on the scan edge, (2,8) and (-4,2): shift == 2 and the "latency shift interior" gate must fail.
- test_weak_instrument_gate_fails: old instrument d*1e-6 + noise was not weak (F is scale invariant, F = 111/81).
  Now pure noise instrument: F = 1.3/1.5, both SW F gates fail by name.


## What changed (bench/ident_fit_yaw.py, bench/tests/test_ident_fit_yaw.py)
- Model alpha = G1 u + G2 du/dt - Dr w + c; rate regressor xr = F[C w] (new `with_rate`, default on; reports `dr`).
- Matched grid (_prepare2): gyro, instrument and u all sampled at u's true update stamps then linearly
  interpolated to the 800 Hz grid, so y, x1, x2, xr, z1, z2 share one interpolation operator.
- Instrument lags widened to 0..64 samples (weak G1/Dr first stage at 0..32).
- This session: decimated test plant now logs u as 400 Hz updates held on 800 Hz stamps (before, u was a 400 Hz
  topic so update_rate gave m = 1 and the m = 2 branch never ran); removed an `or True` no-op assert;
  added a known-answer J test (_gmm_j valid vs invalid instrument).

## K126 MAJORs
- MAJOR-1 (J not chi2): _gmm_j = two-step efficient GMM residuals, df = rank(Zf) - npar. Test: iid known answer.
- MAJOR-2 (df<=0 passes): gate "Hansen df >= 1", jr = inf if df < 1. Test: test_df_gate_fails_when_df_below_one.
- MAJOR-3 (400 Hz interp gain): matched grid. Test: m = 2 closed-loop plant (test_decimated_rate_...).
- MAJOR-4 (no gate-fail tests): shift == delay, boundary, weak F, mismatch-by-gate-name tests present.

## Break-and-restore (copies in scratchpad, production untouched), each test fails when its fix is broken
df gate removed, boundary gate removed, F gate removed, J forced 0, rate column dropped, unmatched gyro grid:
all fail their test (unmatched grid: G1 5406 instead of 205).
