| metric | r1 | r2 | r3 |
|---|---|---|---|
| source ULog | `results/a14_s21/r1/flight.ulg` | `results/a14_s21/r2/flight.ulg` | `results/a14_s21/r3/flight.ulg` |
| arm time (log s) | 30.01 | 30.02 | 30.01 |
| max abs(z_ekf - z_true), arm..arm+20 s [m] | 0.170 | 0.173 | 0.074 |
| time of that max, rel. arm [s] | +6.91 | +7.18 | +4.22 |
| signed residual at that max [m] | -0.170 | -0.173 | +0.074 |
| max abs residual, arm..arm+8 s [m] | 0.170 | 0.173 | 0.074 |
| z_ekf at arm [m, NED down] | -0.003 | -0.000 | +0.047 |
| z_true at arm [m, NED down] | +0.005 | +0.005 | +0.005 |
| z_reset_counter at arm | 2 | 2 | 2 |
| z_reset_counter changes in log (rel. arm) | none | none | none |
| delta_z events, arm..arm+20 s | value at arm -488.051 m; 0 value changes in window; log range [-488.051, -488.051] m | value at arm -488.061 m; 0 value changes in window; log range [-488.061, -488.061] m | value at arm -488.112 m; 0 value changes in window; log range [-488.112, -488.112] m |
| baro_alt_meter change, arm..arm+20 s [m, up] | +5.144 | +5.181 | +5.294 |
| truth altitude change, arm..arm+20 s [m, up] | +5.018 | +4.994 | +5.022 |
| EKF altitude change, arm..arm+20 s [m, up] | +4.992 | +5.002 | +5.008 |
| baro change minus truth change [m] | +0.126 | +0.187 | +0.272 |
| residual arm+55..arm+85 s: max abs [m] | 0.114 | 0.134 | 0.152 |
| residual arm+55..arm+85 s: mean [m] | +0.036 | +0.052 | +0.081 |
| residual arm+55..arm+85 s: rms [m] | 0.057 | 0.072 | 0.091 |
