# Report traces

Small decimated CSV traces for the report figures `step_attitude` and `limits_failures`. They are read from flight logs
that already existed (untracked `flight.ulg` files, paths relative to `indi_flight/results/`); no flight was made for
them. Regenerate with `python3 indi_flight/bench/report_figs/extract_traces.py` where the logs are present (pyulog).
All traces are resampled to 200 Hz (linear interpolation of estimates, zero-order hold of setpoints).

| file | source log | flight it belongs to | signals | window |
|---|---|---|---|---|
| `step_indi_{roll,pitch,yaw}.csv` | `freeze10_s193/steps/seed1/step_{roll,pitch,yaw}_indi/flight.ulg` | FREEZE-10 G2-STEP flights, seed 1, INDI | `att_deg` (vehicle_attitude, Euler angle of the stepped axis, minus pre-step setpoint), `att_sp_deg` (vehicle_attitude_setpoint, same), `rate_dps` (vehicle_angular_velocity), `rate_sp_dps` (vehicle_rates_setpoint) | -0.5 to 1.5 s (yaw 3.0 s) around the first setpoint step, `t_s` = time after the step |
| `step_pid_{roll,pitch,yaw}.csv` | `indi_vs_pid/step_{roll,pitch,yaw}_pid/flight.ulg` | paired PID reference flights (stock rate loop), 800 Hz, seed 1 | same | same |
| `g3_draw3_pitch_rate.csv` | `g3_routeB_s239/ref_s241/{indi,pid}_d3/run_003/flight.ulg` | G3 draw 3 (slow motors), INDI re-fly and PID reference at speed 1 | `q_indi_dps`, `q_pid_dps` (vehicle_angular_velocity pitch rate) | 8 s starting at log time 32.90 s in both logs (the INDI window with the largest 1.5-3 Hz content) |
| `g3_draw264_tilt.csv` | `g3_refly_s199/{indi,pid}_264/run_264/flight.ulg` | G3 draw 264 (saturation with a weak motor), INDI and PID speed-1 flights | `tilt_*_deg` (from vehicle_attitude quaternion), `q_*_dps` (pitch rate) | log time 57.5-62.0 s; `t_s` = time after the fault step (58.683 s) |

The tilt here is the estimated tilt; the chapter's PID maximum (40 deg) comes from the ground-truth tilt over a longer
window.
