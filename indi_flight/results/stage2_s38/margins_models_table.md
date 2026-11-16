# Margins of the linear models (T78), roll axis

Sampled-data L_indi / L_pid (cont.* = continuous e^{-sT} approximation). Defaults: tau_r 0.033, tau_m 0.02, K 20, G1 320,
IMU_GYRO_CUTOFF 40, IMU_DGYRO_CUTOFF 20, d_m 0, lat 0; PID Kp 0.03 Ki 0.06 Kd 0.0006. DM requirement (note 3) = 2 Ts + n Ts.

| controller | config | fs [Hz] | GM [dB] | PM [deg] | DM [ms] | f_c [Hz] | peak S [dB] | band-limited | DM req [ms] |
|---|---|---|---|---|---|---|---|---|---|
| INDI | model-only eta 1 | 800 | 6.1 | 42.7 | 36.5 | 3.25 | 7.3 | no | 3.8 |
| INDI | model-only eta 0.5 | 800 | 3.1 | 33.6 | 48.6 | 1.92 | 11.1 | no | 3.8 |
| INDI | meas Tb 0, n 1, eta 1 | 800 | 21.1 | 54.3 | 55.0 | 2.74 | 3.5 | no | 3.8 |
| INDI | meas+blend Tb 0.1, n 1, eta 1 | 800 | 18.4 | 48.3 | 48.4 | 2.77 | 4.4 | no | 3.8 |
| INDI | meas+blend Tb 0.1, n 1, eta 0.5 | 800 | 16.3 | 52.2 | 108.7 | 1.33 | 3.8 | no | 3.8 |
| PID | roll gains | 800 | 25.8 | 67.9 | 127.4 | 1.48 | 1.1 | no | 2.5 |
| INDI | model-only eta 1 | 400 | 5.8 | 41.6 | 35.2 | 3.28 | 7.6 | no | 7.5 |
| INDI | model-only eta 0.5 | 400 | 3.0 | 33.1 | 47.7 | 1.93 | 11.3 | no | 7.5 |
| INDI | meas Tb 0, n 1, eta 1 | 400 | 34.8 | 54.2 | 55.3 | 2.72 | 3.4 | no | 7.5 |
| INDI | meas+blend Tb 0.1, n 1, eta 1 | 400 | 18.1 | 47.6 | 47.8 | 2.76 | 4.5 | no | 7.5 |
| INDI | meas+blend Tb 0.1, n 1, eta 0.5 | 400 | 15.6 | 51.8 | 107.7 | 1.34 | 3.9 | no | 7.5 |
| PID | roll gains | 400 | 25.1 | 67.7 | 126.9 | 1.48 | 1.1 | no | 5.0 |
| INDI | model-only eta 1 | 267 | 5.5 | 40.6 | 34.1 | 3.31 | 7.9 | no | 11.2 |
| INDI | model-only eta 0.5 | 267 | 3.0 | 32.8 | 47.0 | 1.94 | 11.4 | no | 11.2 |
| INDI | meas Tb 0, n 1, eta 1 | 267 | 33.6 | 54.1 | 55.6 | 2.70 | 3.4 | no | 11.2 |
| INDI | meas+blend Tb 0.1, n 1, eta 1 | 267 | 17.9 | 46.9 | 47.4 | 2.75 | 4.6 | no | 11.2 |
| INDI | meas+blend Tb 0.1, n 1, eta 0.5 | 267 | 15.0 | 51.5 | 107.0 | 1.34 | 3.9 | no | 11.2 |
| PID | roll gains | 267 | 24.4 | 67.4 | 126.5 | 1.48 | 1.2 | no | 7.5 |
| INDI cont.* | model-only eta 1 | 800 | 6.3 | 43.1 | 37.2 | 3.22 | 7.1 | no | - |
| PID cont.* | roll gains | 800 | 26.0 | 67.9 | 127.4 | 1.48 | 1.1 | no | - |
