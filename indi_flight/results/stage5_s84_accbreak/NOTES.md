# S84 T174 stage-output break (MC_INDI_PINJ_PT)
Changed: src/lib/indi_accel_control/{indi_accel_control.cpp,.hpp,IndiAccelControlTest.cpp} (setAppliedThrust + test),
src/modules/mc_indi_pos_control/{McIndiPosControl.cpp,.hpp,mc_indi_pos_control_params.yaml} (MC_INDI_PINJ_PT),
msg/IndiPosStatus.msg (t_c_applied[3]), indi_flight/bench/{pinj_csv.py,tests/test_pinj_csv.py} (--point output).
Tests: unit-IndiAccelControl 31/31 pass; broken once (setAppliedThrust disabled) -> new test fails; restored -> pass.
pinj_csv self-test 4/4; x/y swap in output mode -> PM -43.37 (fail), restored.
Flight (pt1.params, z axis, PT 1, TB 1.0, AMP 0.04, DLY 20, NP 5, seed 1, speed 4, 400 Hz): pt1/ (untracked log),
pt1_pinj_z.csv, pt1_margins.json. Max |u_o| 10.2 m/s^2 (no thrust saturation noted).
Result: PM 58.7 deg, f_c 0.62 Hz, DM 0.262 s, Ms 1.17 (1.33 dB), no -180 crossing in band (top |L| -11.3 dB at 8 Hz).
|L|: 0.2 Hz 4.67, 0.6 1.03, 1.0 0.49, 2 0.27, 3.2 0.07, 4 0.09, 5 0.25, 6.3 0.06, 8 0.30. coh_y low at 3.2-8 Hz (0.12-0.67).
Caveat: output break encloses the outer loops too, so L at low f is the full loop; HF bins are noisy.
Unverified: PT0/AX0 bit-identical flight (by code inspection only), x/y axes, 800 Hz.
