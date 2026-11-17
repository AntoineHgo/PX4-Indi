# T162 a33 split: s72 thrust-gap flights (ULog, same window as second key)

| Metric | gap085_indi_htoff | loss08_indi | loss08_indi_htoff |
|---|---|---|---|
| window (us) | [109771250, 119771250] | [109917500, 119917500] | [110030000, 120030000] |
| mean a_c - a_f x / y / z (m/s^2) | -0.000 / -0.001 / -0.000 | -1.235 / -1.271 / +0.161 | -1.290 / -1.348 / +0.170 |
| mean t_c x / y / z | +0.005 / -0.004 / -11.257 | -1.234 / -1.275 / -9.646 | -1.287 / -1.352 / -10.150 |
| mean t_f x / y / z | +0.005 / -0.003 / -11.257 | +0.001 / -0.004 / -9.807 | +0.003 / -0.004 / -10.320 |
| mean angle t_c vs t_f (deg) | 0.05 | 10.41 | 10.41 |
| fraction blend_frozen true | 0.000 | 0.000 | 0.000 |
| mean blend | 0.0240 | 0.0084 | 0.0084 |
| mean thrust | +0.1608 | +0.1452 | +0.1452 |
| tilt setpoint q_d (deg) | 0.14 | 10.42 | 10.42 |
| tilt actual q (deg) | 0.14 | 0.14 | 0.15 |
| mean angle body z: setpoint vs actual (deg) | 0.05 | 10.41 | 10.41 |
| mean actuator_motors control[0..3] | 0.161 / 0.161 / 0.161 / 0.161 | 0.137 / 0.137 / 0.171 / 0.137 | 0.137 / 0.137 / 0.171 / 0.137 |
| mean esc_status rpm per motor | m0 9535, m1 9535, m2 9536, m3 9536, m4 0, m5 0, m6 0, m7 0, m8 0, m9 0, m10 0, m11 0 | m0 9537, m1 9537, m2 9537, m3 9537, m4 0, m5 0, m6 0, m7 0, m8 0, m9 0, m10 0, m11 0 | m0 9537, m1 9537, m2 9537, m3 9537, m4 0, m5 0, m6 0, m7 0, m8 0, m9 0, m10 0, m11 0 |

## Method

- Window: same as second_key (last 10 s before landing start, from analyse()). All indi_pos_status, actuator_motors and esc_status samples inside it are used directly; no interpolation for those.
- Vector angles (t_c vs t_f, body z setpoint vs actual) are per sample; the means are over the samples.
- Attitude: body z (third column of the body-to-NED rotation of q_d or q) is interpolated linearly onto the 100 Hz window grid by timestamp, then normalised. Tilt = angle between body z and NED down.
- blend_frozen fraction is over indi_pos_status samples in the window; blend and thrust are sample means.
- esc rpm is the mean over esc_status samples in the window for each esc[i].esc_rpm present in the log.
