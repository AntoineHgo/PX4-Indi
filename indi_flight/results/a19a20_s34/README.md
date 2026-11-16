# S34 pre-test: A-19 / A-20 bench params (partial: 1 of 3 runs read in S34)

Script `bench/a19a20_pretest_s34.sh`, params `bench/a19a20_pretest_s34.params` (SENS_BAR_AUTOCAL 0, EKF2_DECL_TYPE 0,
EKF2_MAG_DECL 2.62, EKF2_MAG_B_NOISE 0), speed 4, seed 1, B32 flags. Params confirmed in the ULog initial parameters
of hover_r1 (meta `params_applied` lookup returned None: read the right json in S35).

## hover_r1 (S34, by hand)
- A-20 / A-14 (`a14_close_check.py`): p0 95593 Pa, CAL_BARO0_OFF 0.0/0.0, bias0 0.15 m, bias@arm 0.12 m, baro_fault 0,
  max |z_ekf - z_true| 15-35 s 0.068 m, PASS. With autocal off the offset calibration no longer varies the bias.
- A-19 (`a19_mech.py hover_r1`): EKF declination in window 3.67 deg (param 2.62, sensor field 2.77), err align+1 s
  -0.44, at arm +0.22, window +0.52 deg (sd 0.05), magB_x -5.8 mG despite EKF2_MAG_B_NOISE 0.
  => closing criteria NOT met (0.2 / 0.3 deg, 0.5 mG). The T68 fix candidate is refuted in its simple form: in 3-axis
  mag fusion the EKF estimates the earth field (declination drifts from the param) and the body bias states move
  from their initial variance even with zero process noise. Error sign flipped (+0.5 vs -0.6..-1.4 deg in B32).

## S35
Read hover_r2, step_roll_r1 (`status.txt`, `a14_check.md`, `python3 a19_mech.py`). If A-20 holds in all 3: run the
15-run set with SENS_BAR_AUTOCAL 0 alone + two keys, then close A-20. A-19: next candidate EKF2_MAG_TYPE heading-only
(no earth/bias states) or EKF2_DECL_TYPE with cs_mag_dec fusion; else park A-19 by mechanism (EKF earth-field and
bias estimation in 3-axis mode) and report yaw on the estimate with the heading error separately (Q4 option A).
