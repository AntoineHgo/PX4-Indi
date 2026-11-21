# A-51 closing test: gz/ESC latency added to the rate model, x-check re-run (15 groups)

## 1. Measured latency and source
No earlier result measured the command-to-rotor-speed latency (results/ and design/ only give the eRPM telemetry frame, `SIM_GZ_ERPM_LAT` 0 = one output frame). Measured here on the freeze ulgs
`roll400_s1/s1/flight.ulg` and `roll800_s1/s1/flight.ulg` (v2 sim, esc_status instance 0 = the only logged one, esc_rpm = gz joint speed), window 60-70 s, with
`indi_flight/bench/a51_motor_latency.py` (fit rpm = a + b LP1_tau(cmd(t-d)), grid d 0-30 ms, tau 15-60 ms, 0.1 ms grid, per motor).
- 400 Hz: d = 4.1 ms (tau fixed 33 ms, motors 4.0/4.0/4.0/4.5); free fit tau 41-45 ms, d = 3.6 ms.
- 800 Hz: d = 2.1 ms (tau fixed 33 ms, motors ~2.0); free fit tau 40-43 ms, d = 1.6 ms.
Both are about 1.6-1.7 output frames (frame = 2.5 / 1.25 ms). Caveat: d is the lag seen in the log, so it includes the one-frame eRPM telemetry reply and the physics-step
sample-and-hold; the plant itself may carry less. Used below: 2.1 ms (800 Hz), 4.1 ms (400 Hz), applied to the plant and measured-torque path (`lat_s`).

## 2. Model change
`bench/margins_models.py`: new keyword `lat_s` (seconds, fractional samples allowed, default 0 = old behaviour) added to `lat` in L_indi, L_indi_yaw, L_pid.
`bench/tests/test_margins_selftest.py`: new test7_pure_delay (L_pid: f_c unchanged, PM drop = 360 f_c T deg for T 2.0 and 4.1 ms at 800/400 Hz, within 0.01 deg). All tests pass.
`bench/g2_rate_model_s165.py`: new flag `--lat-ms=800:2.1,400:4.1`. Without it the output is byte-identical to the old xcheck_rate.md (checked with git diff).

## 3. Before / after (measured = mean over seeds; agree = within 10 deg PM and 3 dB GM for every seed)
| cell | measured GM / PM | model before (lat 0) GM / PM | agree | model after GM / PM | agree |
|---|---|---|---|---|---|
| roll800 (n=3) | 18.9 / 56.4 | 17.6 / 58.4 | yes | 15.2 / 55.5 | NO |
| roll400 (n=3) | 15.0 / 55.8 | 17.9 / 57.3 | NO | 13.6 / 51.8 | yes |
| pitch800 (n=3) | 18.8 / 56.1 | 17.6 / 58.4 | yes | 15.2 / 55.5 | NO |
| pitch400 (n=3) | 15.4 / 55.9 | 17.9 / 57.3 | yes | 13.6 / 51.8 | yes |
| yaw800 (n=2) | 19.9 / 79.1 | 20.1 / 71.5 | yes | 17.2 / 68.9 | NO |
| yaw400 (n=2) | 15.3 / 81.1 | 21.5 / 71.8 | NO | 16.3 / 66.8 | NO |
| roll800 model-only (n=2) | 13.8 / 56.0 | 15.5 / 57.9 | yes | 11.2 / 53.9 | yes |
| roll400 model-only (n=2) | 11.9 / 54.6 | 14.1 / 56.2 | yes | 7.9 / 48.0 | NO |
| pitch800 model-only (n=2) | 13.8 / 55.8 | 15.5 / 57.9 | yes | 11.2 / 53.9 | yes |
| pitch400 model-only (n=2) | 12.1 / 54.7 | 14.1 / 56.2 | yes | 7.9 / 48.0 | NO |
| yaw800 model-only (n=2) | 18.0 / 76.1 | 17.9 / 70.7 | yes | 12.8 / 66.5 | NO |
| yaw400 model-only (n=2) | 17.0 / 75.6 | 17.9 / 70.3 | yes | 9.8 / 61.8 | NO |
| roll800 fwdef (n=3) | 16.2 / 54.3 | 17.1 / 65.9 | NO | 13.7 / 64.8 | NO |
| att yaw 800 (n=2) | 30.5 / 81.4 | 29.9 / 82.2 | yes | 28.1 / 82.2 | yes |
| att yaw 400 (n=2) | 30.9 / 81.4 | 28.5 / 81.8 | yes | 25.7 / 81.8 | NO |

Agreement: before 12/15, after 5/15.

## 4. Verdict
Not closed, and the latency hypothesis is rejected as the explanation. Adding the measured latency lowers the model GM by about 2.5-3 dB at 800 Hz and 4.3 dB at 400 Hz, but the
800 Hz model already agreed (18.9 measured vs 17.6 model) and now undershoots (15.2), so 800 Hz cells flip to NO. At 400 Hz it brings roll400 into agreement (13.6 vs 15.0 measured) but
the 800-to-400 GM drop in the model is only ~1.6 dB against 3.9 dB measured, and the model-only 400 cells (7.9 vs 11.9 dB) and yaw cells overshoot. Yaw400: GM 16.3 vs 15.3 now agrees, but
yaw PM gets worse (66.8 vs 81.1, 14 deg low): latency can only lower model PM, so the yaw PM residual (model 7-10 deg low before the change) is a separate structural error in the yaw model
(most likely the reaction-torque path: ts_fw = G2/G1 = 27/205 and its filter D(z), not the motor delay). The roll800 fwdef PM residual (+10.5 to +11.6 deg, model high) has the opposite sign and
is also not a delay effect (fwdef = ID_OK 0, K x 0.5, ACT_TC 0.05, model path; model PM 65 vs measured 54). Likeliest cause for the remaining rate-dependent GM gap: the measured GM is set by a
high-frequency phase crossing where the log-based latency (which includes telemetry reply, so not all of it is in the plant) and the 40/20 Hz filter assumptions (UNVERIFIED vs IMU_*_CUTOFF) dominate.
No further chase done.

Reopen check: no measured cell nears 6 dB / 45 deg (measured minimum 11.9 dB GM, 54.3 deg PM, unchanged by this test since only the model moved). The worst model cell with latency is 7.9 dB / 48.0 deg
(roll/pitch400 model-only), still above the thresholds. G2 bound stands; A-51 residuals remain unexplained, not closed.

## 5. Commands
```
indi_project/docker/run.sh -n a51 -t 600 -- python3 indi_flight/bench/a51_motor_latency.py indi_flight/results/g2_freeze_s160/roll400_s1/s1/flight.ulg 60 70
indi_project/docker/run.sh -n a51 -t 600 -- python3 indi_flight/bench/a51_motor_latency.py indi_flight/results/g2_freeze_s160/roll800_s1/s1/flight.ulg 60 70
python3 indi_flight/bench/tests/test_margins_selftest.py
python3 indi_flight/bench/g2_rate_model_s165.py                       # before (rewrites xcheck_rate.md, unchanged)
python3 indi_flight/bench/g2_rate_model_s165.py --lat-ms=800:2.1,400:4.1   # after (script writes xcheck_rate_a51_table.md, folded into section 3)
```
