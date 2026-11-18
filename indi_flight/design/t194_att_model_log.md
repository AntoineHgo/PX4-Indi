# T194 attitude-loop linear model log

- Added L_att_indi / L_att_pid (+ helpers _att_path, _pn) to bench/margins_models.py; existing functions untouched.
- Tests: bench/tests/test_att_model.py (no pytest on host; run `python3 bench/tests/test_att_model.py`): identity INDI/PID, att_p->0, DC unity T_cl, ideal-integrator margins: all pass. scipy missing on host, not needed.
- Table: bench/att_model_vs_measured.py -> results/stage5_s91_attbreak/model_vs_measured.md.
- Params: pt1.params has no MC_ROLL_P / rate gains; airframe 4040_gz_quad5in defaults used (att_p 8, PID 0.03/0.06/0.0006).
- mc_att_control is vehicle_attitude-callback driven (mc_att_control_main.cpp:83), not rate-loop-rate: att_lat=1 is a placeholder.
- Yaw not modelled (yaw LPFs in rate loop, MC_YAW_WEIGHT).
- Result: roll/pitch dPM -14..-15 deg (FAIL, model PM ~72 vs meas ~57), dGM <= 2.9 dB; anomaly to log.
