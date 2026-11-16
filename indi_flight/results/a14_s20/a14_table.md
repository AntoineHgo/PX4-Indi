| metric | orig_pretest_s18 | r1 | r2 |
|---|---|---|---|
| source ULog | `indi_flight/results/a12_fix_s18/pretest_truth_topics/hover/flight.ulg` | `indi_flight/results/a14_s20/r1/flight.ulg` | `indi_flight/results/a14_s20/r2/flight.ulg` |
| arm time (log s) | 30.01 | 30.02 | 30.01 |
| max abs(z_ekf - z_true), arm..arm+20 s [m] | 2.218 | 2.283 | 0.199 |
| time of that max, rel. arm [s] | +1.18 | +1.47 | +7.05 |
| signed residual at that max [m] | -2.218 | -2.283 | -0.199 |
| max abs residual, arm..arm+8 s [m] | 2.218 | 2.283 | 0.199 |
| z_ekf at arm [m, NED down] | -2.200 | -2.277 | -0.009 |
| z_true at arm [m, NED down] | +0.005 | +0.005 | +0.005 |
| z_reset_counter at arm | 2 | 2 | 2 |
| z_reset_counter changes in log (rel. arm) | none | none | none |
| delta_z events, arm..arm+20 s | value at arm -488.040 m; 0 value changes in window; log range [-488.040, -488.040] m | value at arm -488.017 m; 0 value changes in window; log range [-488.017, -488.017] m | value at arm -488.022 m; 0 value changes in window; log range [-488.022, -488.022] m |
| baro_alt_meter change, arm..arm+20 s [m, up] | +7.746 | +7.585 | +5.408 |
| truth altitude change, arm..arm+20 s [m, up] | +7.205 | +7.227 | +4.969 |
| EKF altitude change, arm..arm+20 s [m, up] | +5.032 | +5.003 | +5.002 |
| baro change minus truth change [m] | +0.541 | +0.358 | +0.439 |
| residual arm+55..arm+85 s: max abs [m] | 0.089 | 0.072 | 0.072 |
| residual arm+55..arm+85 s: mean [m] | +0.039 | -0.010 | -0.013 |
| residual arm+55..arm+85 s: rms [m] | 0.056 | 0.037 | 0.041 |
