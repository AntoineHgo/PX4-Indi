# T192 ratesp_csv.py log

- Read pinj_csv.py, attitude_break_check.load(), attitude_break_s86.md section 6.
- bench/ratesp_csv.py: own load() (indi_rate_status, timestamp_sample), window() on d != 0, reuses margins_est.frf_periodic /
  margins_from_frf by import (pinj_csv.py untouched). CSV f_hz,L_db,arg_L_deg,coh,L_spread,accepted. --margins JSON:
  pm_deg, gm_db, f_c_hz, validity (max|x-y-d|, window_len_s, n_periods_complete, max_gap).
- tests/test_ratesp_csv.py: L0 = K e^{-s tau}/s (K=4pi, tau=0.02 -> f_c 2 Hz, PM 75.6 deg), 4 tests: known loop
  (PM within 1 deg, f_c within 5 %), noise, swapped x/y detected (PM/crossing wrong, x-y-d check > 1e-3), window gate.
- First run failed: test excited a different bin grid than the estimator's log_bins (junk bins). Fixed by using me.log_bins.
- Docker pytest: 4 passed. Not run: the CLI on a real .ulg (no pyulog fixture); the s86 checks on y vs held setpoint,
  d vs generator, fault/landed are not implemented (need extra topics / generator).
