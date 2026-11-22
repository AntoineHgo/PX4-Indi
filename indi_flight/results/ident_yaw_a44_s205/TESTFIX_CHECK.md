# Test-fix check (S205): test_ident_fit_yaw.py vs key2 MAJOR-1 / MINOR-1 / MINOR-3

pytest is not installed; tests run as plain python via a runner (scratchpad run.py: imports the test file, calls each test_*).
Command: `cd indi_flight; ulimit -v 4000000; timeout 1500 python3 -I /tmp/claude-1001/yawk2_check/run.py $PWD/bench/tests/test_ident_fit_yaw.py`
Total 614 s. All 14 tests PASS (s): recovers 181, omitting_du_dt 53, no_spinup 59, mismatched_filter 60, decimated_rate_intercept 34
(now shift == 0), decimated_shift_exact 21, ci_too_wide_gate_fails_by_name 15, gmm_j_is_two_step_not_2sls 0,
rate_regressor_on_matched_grid 0, omitting_rate_term 16, shift_value_and_boundary 140, weak_instrument 36, df_gate 1,
gmm_j_valid_vs_invalid 0.

## Mutants (copies in /tmp/claude-1001/yawk2_check/{M8,M6,M10}/, production file untouched)
- M8 CI/|G1| gate forced True: KILLED by test_ci_too_wide_gate_fails_by_name (AssertionError, failing-gate list empty).
- M6 J from 2SLS residuals (e2 = res_2sls in _gmm_j): KILLED by test_gmm_j_is_two_step_not_2sls (J 6.14 vs 2SLS-J 4.04).
- M10 xr from raw 800 Hz gyro: KILLED by test_rate_regressor_on_matched_grid (max dev 0.46 of column std).
Not run: M4 (decimated shift off-by-one) was not requested; test_decimated_shift_exact is new for it, unverified by mutant.

## V0 "synthetic 597"
NOT explained. results/ident_m3a_s123/a43_probe/README.md:27 lists S0 (=V0) G1 596.9; :35 only says "on synthetic V0 is unreliable (597),
so the interpolation effect is not cleanly characterised". design/key2 note and results/ident_yaw_fix_s202 have no 597 entry
(s202/README.md:40 reports a different number, unmatched grid G1 5406 vs 205).
