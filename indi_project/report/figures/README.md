# Report figures

All figures are regenerated from recorded data by one script, with no arguments, from the repo root:

    python3 indi_project/bench/make_figures.py

Needs numpy, matplotlib and pyulog (the time series only). Use plain `python3`, not `python3 -I`: on the host
matplotlib and pyulog live in the user site-packages, which isolated mode ignores. The script prints the plotted
numbers and compares them with the reference markdown tables in `results/` (flag `DISCREPANCY` above 2 %).
Colours: PID default = blue, INDI tuned = red, in every figure. Loading helpers and metric keys come from
`bench/summarize_seeds.py` (imported by path).

Ratio figures: one red dot per seed, ratio = INDI / PID for the same seed (paired by seed, 10 seeds each); bar and
number = median of the paired ratios; blue line = PID = 1; log y axis. Below 1 means INDI is better.

## fig_attitude_ratio.png
INDI/PID ratio of each scenario's primary tracking metric. Metric per scenario (JSON key in `metrics.json`):
- attitude rotation-angle RMS (`attitude_tracking.rotation_angle_rms_deg`): com_shift, gust_diag, gust_x,
  payload_add, mismatch_inertia, step_diag, motor_loss_0, mismatch_combined_att
- roll-rate RMS (`rate_tracking.roll_rms_rad_s`): mismatch_combined_rate (the T4 primary metric of the H5 table)
- 3D position RMS (`trajectory.rms_3d_m`, against the logged trajectory setpoint): traj_lemniscate, traj_circle_fast

Data: `results/runs/<scenario>/{pid_default,indi_tuned}/seed*/metrics.json`.
References: `results/heldout_s14.md`, `heldout_s15.md`, `heldout_h5_s15.md`, `acceptance_s15.md`,
`t8_motor_loss_s13.md`.

## fig_effort_ratio.png
Same layout, control effort = motor-rate RMS (`effort.motor_rate_rms_per_s`, 1/s). Same data and references
(no effort reference exists in the md files for traj_lemniscate and traj_circle_fast; plotted unverified).

## fig_act_tc_sweep.png
Roll-rate RMS (rad/s, `rate_tracking.roll_rms_rad_s`) and motor-rate RMS (1/s) versus the MC_INDI_ACT_TC factor f
(0.33 ... 3, f = 1 is the frozen 0.01142 s), step_roll, speed 4, seeds 1-3; small dots are seeds, line is the seed
mean, blue line is the PID mean on the same seeds. Data: `results/runs/step_roll/indi_act<f>/seed*_x4/` and
`results/runs/step_roll/pid_default/seed*_x4/` (the `seed*` speed-1 dirs of pid_default are not used).
Reference: `results/act_tc_sweep_s17.md`.

## fig_rate_timeseries.png
Roll rate (deg/s, `vehicle_angular_velocity` xyz[0]) against the roll-rate setpoint (`vehicle_rates_setpoint` roll)
for mismatch_combined_rate, seed 1, over the metrics window (`window.start_s`..`end_s`), PID on top, INDI below.
Data: `results/runs/mismatch_combined_rate/{pid_default,indi_tuned}/seed1_x4/{flight.ulg,metrics.json}`.
Shows the 5-7 Hz ringing after each pulse that explains the INDI ratio of 1.58 in the first figure.

## Left out
Nothing: both controllers have data for all 11 scenarios.

## Discrepancies
None above 2 % (largest 1.8 %, com_shift: ratio of means 0.157 vs md 0.16, which is md rounding to 2 digits).
Notes on how the check was done:
- The md ratios are mean(INDI)/mean(PID); the plotted bars are medians of per-seed ratios, so they can differ from
  the md numbers (e.g. mismatch_combined_att effort 3.32 median vs 3.08 ratio of means; com_shift 0.162 vs 0.157).
  The check compares the ratio of means from the same runs with the md value.
- motor_loss_0: runs contain 10 seeds but `t8_motor_loss_s13.md` lists seeds 1-3 only; the reference ratios
  (attitude 1.138, effort 1.298) were computed by hand from its per-seed table, and compared on seeds 1-3.
- mismatch_combined_att: reference attitude ratio 0.91 is from `acceptance_s15.md` (stepped-axis attitude RMS);
  the 3.86 in `heldout_h5_s15.md` is a roll-rate RMS and is not plotted.
- Unverified: effort ratios of traj_lemniscate (0.87 median) and traj_circle_fast (0.95).
