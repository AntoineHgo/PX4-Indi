# S35: A-20 closing set and A-19 heading-only pre-test

Script `bench/a20a19_s35.sh` (speed 4, seed 1, B32 flags, hover), 17/17 flew (docker_rc 0, ~40 s wall each).

## A-20 (15 hovers, `bench/a20_close_s35.params`: SENS_BAR_AUTOCAL 0 alone) -> `a20/a14_check.md`
- CAL_BARO0_OFF 0.0/0.0 in 15/15; baro_fault 0 in 15/15; p0 95589-95600 Pa.
- Median baro bias over [arm - 5 s, arm] 0.11-0.16 m in 15/15 (< 0.5 m). Column second-keyed: T70 AGREE 7/7
  (`second_key_t70.md`).
- => A-20 closing criteria MET. CLOSED. Bench param set keeps SENS_BAR_AUTOCAL 0 (stock baro-to-GNSS offset
  calibration, a one-sample bisection, was the run-to-run source).
- The script's overall FAIL is the A-14 test as originally written (0.1 m / 0.05 m): max |z_ekf - z_true| 15-35 s
  0.047-0.119 m (A-14 parked bound 0.15 m: holds), hold -4.925..-5.033 m, one run 0.068 m from the median
  (parked bound +-0.06 m: EXCEEDED by 8 mm, r14). Hold altitude is a truth quantity of the PID position loop on an
  EKF height with ~0.1 m noise; see A-14 note.

## A-19 (2 hovers, `bench/a19_magtype_s35.params`: + EKF2_MAG_TYPE 1 heading-only, decl 2.62) -> `a19/`
Quick truth-minus-EKF yaw (`bench/a19_yaw_quick_s35.py`, own script, not second-keyed; on S34 hover_r1 it gives
+0.54 vs a19_mech +0.52 deg):
| run | pre-arm 25-30 s | window 45-60 s (sd) |
|---|---|---|
| a19/hover_r1 | +0.36 | +0.73 (0.04) |
| a19/hover_r2 | -0.10 | +0.51 (0.06) |
| a20/r1 (stock mag) | -0.62 | -0.42 (0.03) |
| a20/r2 (stock mag) | -0.98 | -1.08 (0.03) |
- Heading-only fusion does not remove the error (> 0.3 deg) and it still moves by ~0.4-0.6 deg between pre-arm
  and the hover window. Candidate refuted. A-19 PARKED (route check 35), see ANOMALIES.
