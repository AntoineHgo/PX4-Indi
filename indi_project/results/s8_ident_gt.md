# S8 identification of outer-loop thrust constants (G_T, k_cmd) from hover logs

Status: plan written before any analysis. Per-log result lines are appended by
`indi_project/bench/ident_gt.py` as each log is computed. Identification only,
nothing tuned.

## Plan and definitions

- Per log, every topic is resampled onto `esc_status` timestamps (previous-value hold).
- `mean_u = mean_i (omega_i / omega_max)^2`, `omega_i = esc[i].esc_rpm * 2*pi/60`,
  `omega_max = 1000 rad/s` (CA_R_W_MAX). Samples with any rpm <= 0 are skipped.
- `f = |sensor_combined.accelerometer_m_s2[0..2]|` (m/s^2), low-passed at full
  sensor rate before resampling. Filter: scipy `butter(2, 5 Hz)` zero-phase if
  scipy is importable, otherwise a centred 0.2 s moving average. The host has no
  scipy, so the moving average is the one used (recorded per log in the line).
- `T = -vehicle_thrust_setpoint.xyz[2]`; if that topic is absent, k_cmd is skipped.
- Fits, least squares through the origin:
  - `G_T`: `f ~ G_T * mean_u`. Also `mean(f)/mean(mean_u)`.
  - `k_cmd`: `mean_u ~ k_cmd * T`.
  - R^2 is centred on the response; residual std is reported in m/s^2 (or dimensionless for k_cmd).
- Hover window: `run.json` `hold` event (`t_us`, `dur_s`) intersected with
  not landed, |vz| < 0.3 m/s, |vx|, |vy| < 0.5 m/s, and t >= takeoff + 5 s.
  If the window leaves fewer than 100 samples, the filters alone are used and the line says so.

## Log set

- Scenario `hover`, `s2_seen_v2/runs/hover/{pid_tuned,indi_v2}/seed{1..5}/flight.ulg`, 10 logs.
  This is the cap of 10 logs from the brief.
- Not used: `s2_heldout_v2/runs/v2_vib3_hover/*`. Same controllers and seeds, but it is a
  vibration-injection variant, which is outside the plain hover condition that this
  identification targets. The 10-log cap is the reason it is excluded.
- Unparseable or incomplete logs are listed as failures below.

## Per-log results

- `indi_project/results/s2_seen_v2/runs/hover/pid_tuned/seed1/flight.ulg` [pid_tuned/seed1]: n=6000, G_T=16.568 (R2=0.4575, resid_std=0.009 m/s^2), mean(f)/mean(mean_u)=16.568, G_T*mean(mean_u)=9.823 m/s^2, k_cmd=0.9993 (R2=0.7397, resid_std=0.0004); takeoff=17.68s; window: run.json hold 34.9-64.9s; filter: moving_average_0.2s
- `indi_project/results/s2_seen_v2/runs/hover/pid_tuned/seed2/flight.ulg` [pid_tuned/seed2]: n=6000, G_T=16.586 (R2=0.4709, resid_std=0.012 m/s^2), mean(f)/mean(mean_u)=16.586, G_T*mean(mean_u)=9.835 m/s^2, k_cmd=0.9994 (R2=0.7120, resid_std=0.0004); takeoff=13.37s; window: run.json hold 31.6-61.6s; filter: moving_average_0.2s
- `indi_project/results/s2_seen_v2/runs/hover/pid_tuned/seed3/flight.ulg` [pid_tuned/seed3]: n=6001, G_T=16.966 (R2=0.3815, resid_std=0.011 m/s^2), mean(f)/mean(mean_u)=16.966, G_T*mean(mean_u)=10.057 m/s^2, k_cmd=0.9992 (R2=0.6961, resid_std=0.0004); takeoff=18.69s; window: run.json hold 35.9-65.9s; filter: moving_average_0.2s
- `indi_project/results/s2_seen_v2/runs/hover/pid_tuned/seed4/flight.ulg` [pid_tuned/seed4]: n=6000, G_T=16.926 (R2=0.4894, resid_std=0.014 m/s^2), mean(f)/mean(mean_u)=16.926, G_T*mean(mean_u)=10.034 m/s^2, k_cmd=0.9992 (R2=0.7362, resid_std=0.0004); takeoff=17.87s; window: run.json hold 36.1-66.1s; filter: moving_average_0.2s
- `indi_project/results/s2_seen_v2/runs/hover/pid_tuned/seed5/flight.ulg` [pid_tuned/seed5]: n=6001, G_T=16.530 (R2=0.3588, resid_std=0.009 m/s^2), mean(f)/mean(mean_u)=16.530, G_T*mean(mean_u)=9.801 m/s^2, k_cmd=0.9994 (R2=0.6547, resid_std=0.0005); takeoff=18.49s; window: run.json hold 35.7-65.7s; filter: moving_average_0.2s
- `indi_project/results/s2_seen_v2/runs/hover/indi_v2/seed1/flight.ulg` [indi_v2/seed1]: n=5850, G_T=16.527 (R2=0.9318, resid_std=0.009 m/s^2), mean(f)/mean(mean_u)=16.527, G_T*mean(mean_u)=9.786 m/s^2, k_cmd=0.9997 (R2=0.9136, resid_std=0.0006); takeoff=17.63s; window: run.json hold 34.9-64.9s; filter: moving_average_0.2s
- `indi_project/results/s2_seen_v2/runs/hover/indi_v2/seed2/flight.ulg` [indi_v2/seed2]: n=6001, G_T=16.721 (R2=0.4673, resid_std=0.016 m/s^2), mean(f)/mean(mean_u)=16.721, G_T*mean(mean_u)=9.913 m/s^2, k_cmd=0.9993 (R2=0.6771, resid_std=0.0005); takeoff=17.97s; window: run.json hold 35.3-65.3s; filter: moving_average_0.2s
- `indi_project/results/s2_seen_v2/runs/hover/indi_v2/seed3/flight.ulg` [indi_v2/seed3]: n=6000, G_T=16.677 (R2=0.3390, resid_std=0.012 m/s^2), mean(f)/mean(mean_u)=16.677, G_T*mean(mean_u)=9.887 m/s^2, k_cmd=0.9993 (R2=0.7359, resid_std=0.0004); takeoff=18.48s; window: run.json hold 36.7-66.7s; filter: moving_average_0.2s
- `indi_project/results/s2_seen_v2/runs/hover/indi_v2/seed4/flight.ulg` [indi_v2/seed4]: n=6001, G_T=16.677 (R2=0.3394, resid_std=0.019 m/s^2), mean(f)/mean(mean_u)=16.677, G_T*mean(mean_u)=9.886 m/s^2, k_cmd=0.9993 (R2=0.5844, resid_std=0.0005); takeoff=18.03s; window: run.json hold 35.2-65.2s; filter: moving_average_0.2s
- `indi_project/results/s2_seen_v2/runs/hover/indi_v2/seed5/flight.ulg` [indi_v2/seed5]: n=5859, G_T=16.558 (R2=0.9127, resid_std=0.011 m/s^2), mean(f)/mean(mean_u)=16.558, G_T*mean(mean_u)=9.804 m/s^2, k_cmd=0.9996 (R2=0.9073, resid_std=0.0006); takeoff=18.60s; window: run.json hold 35.8-65.8s; filter: moving_average_0.2s

## Summary, median [min, max] across logs

- all logs (n_logs=10): G_T=16.631 [16.527, 16.966]; G_T*mean(mean_u)=9.861 [9.786, 10.057] m/s^2; k_cmd=0.9993 [0.9992, 0.9997] (n=10)
- indi_v2 (n_logs=5): G_T=16.677 [16.527, 16.721]; G_T*mean(mean_u)=9.886 [9.786, 9.913] m/s^2; k_cmd=0.9993 [0.9993, 0.9997] (n=5)
- pid_tuned (n_logs=5): G_T=16.586 [16.530, 16.966]; G_T*mean(mean_u)=9.835 [9.801, 10.057] m/s^2; k_cmd=0.9993 [0.9992, 0.9994] (n=5)

## Notes and verdict

- Logs analysed: 10 of 10. Parse or analysis failures: none.
- Low-pass: scipy is not importable on the host, so the 0.2 s moving-average fallback was used for every log.
- Window check: the run.json hold window gives n of about 6000 per log, matching 30 s at the 200 Hz esc_status rate, so the run.json time base lines up with the ULog time base.
- Fit quality: R^2 is centred on f and is low (0.34 to 0.93) because hover specific force is dominated by noise. The residual std is 0.01 to 0.02 m/s^2, and k_cmd residuals are about 0.0005.
- Verdict: the median of G_T*mean(mean_u) is 9.86 m/s^2 (range 9.79 to 10.06), within about 0.5% of 9.81 m/s^2. That is consistent with hover, where the fitted mean specific force equals gravity.
