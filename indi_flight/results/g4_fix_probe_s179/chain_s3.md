#### indi_flight/results/g4_fix_probe_s179/f1_lpf5_s3/flight.ulg
logged Hz: pos_sp/lpos_sp x,y,z,v 89, lpos (estimate) 89, outer a_c (indi_pos) 89, outer a_f (filt spec.force) 89, outer t_c/t_c_applied 89, att_sp q_d,thrust_body 89, rates_sp (267Hz) 266, vehicle_acceleration 267, gyro (angular_velocity) 799, inner nu/alpha_f/tau_f 799, inner dtau/rates_sp_applied 799, torque_setpoint 799, thrust_setpoint 799, torque_measured 799, actuator_motors 799
| signal | comp | ctl(18-28) | L1(38-52) | L2d(62-66.5) | L2g(69.5-72) |
|---|---|---|---|---|---|
| pos_sp/lpos_sp x,y,z,v | thrust[1] | 32.6Hz x1.4 rms1.2e-06 | 33.1Hz x127.5 rms7.1e-04 | 18.7Hz x42851.0 rms4.7e-04 | 18.2Hz x5.9 rms4.6e-12 |
| lpos (estimate) | ax | 32.6Hz x1.5 rms1.2e-03 | 34.7Hz x1.0 rms3.0e-03 | 18.7Hz x69756.7 rms3.7e-01 | 18.2Hz x24.5 rms3.1e-03 |
| outer a_c (indi_pos) | a_c[1] | 32.6Hz x1.1 rms8.0e-05 | 33.1Hz x137.2 rms6.6e-02 | 18.7Hz x53409.1 rms3.3e-02 | 18.2Hz x0.0 rms0.0e+00 |
| outer a_f (filt spec.force) | a_f[1] | 30.6Hz x1.1 rms2.0e-05 | 30.6Hz x1.4 rms3.4e-04 | 18.7Hz x33917.8 rms5.9e-03 | 24.2Hz x5.3 rms1.1e-07 |
| outer t_c/t_c_applied | t_c[1] | 32.6Hz x1.3 rms8.2e-05 | 33.1Hz x137.6 rms6.6e-02 | 18.7Hz x52558.1 rms3.6e-02 | 18.2Hz x19.3 rms3.7e-10 |
| att_sp q_d,thrust_body | q_d[1] | 36.7Hz x1.5 rms3.9e-06 | 33.1Hz x121.2 rms1.9e-03 | 18.7Hz x38674.2 rms1.7e-03 | 18.2Hz x12.3 rms1.2e-09 |
| rates_sp (267Hz) | pitch | 36.5Hz x1.3 rms1.3e-05 | 33.0Hz x32.3 rms1.3e-03 | 18.7Hz x24799.8 rms4.4e-03 | 23.1Hz x11.2 rms8.1e-06 |
| vehicle_acceleration | xyz[0] | 33.5Hz x8.6 rms7.0e-04 | 30.0Hz x3.2 rms8.8e-04 | 19.4Hz x2.8 rms1.8e-03 | 18.0Hz x395.5 rms4.3e-03 |
| gyro (angular_velocity) | xyz[0] | 31.5Hz x8.7 rms1.4e-04 | 32.5Hz x9.2 rms1.7e-04 | 18.7Hz x290.1 rms8.1e-04 | 20.0Hz x6.0 rms1.4e-04 |
| inner nu/alpha_f/tau_f | nu[1] | 33.5Hz x7.8 rms3.5e-03 | 33.5Hz x49.5 rms6.9e-02 | 18.7Hz x7339.6 rms1.1e-01 | 22.0Hz x10.2 rms2.8e-03 |
| inner dtau/rates_sp_applied | torque_increment[0] | 31.5Hz x5.2 rms1.5e-05 | 33.0Hz x25.4 rms1.1e-04 | 18.7Hz x1578.4 rms2.4e-04 | 20.0Hz x4.1 rms8.1e-06 |
| torque_setpoint | xyz[0] | 31.5Hz x5.5 rms1.6e-05 | 33.0Hz x27.8 rms1.1e-04 | 18.7Hz x1215.4 rms2.1e-04 | 20.0Hz x4.2 rms8.2e-06 |
| thrust_setpoint | xyz[2] | 32.0Hz x758.9 rms1.9e-05 | 33.5Hz x961.3 rms5.9e-04 | 22.0Hz x438.6 rms2.5e-05 | 18.0Hz x9.9 rms3.1e-06 |
| torque_measured | torque[1] | 33.5Hz x6.9 rms8.8e-06 | 33.5Hz x6.6 rms2.4e-05 | 18.7Hz x96.5 rms4.8e-05 | 19.0Hz x27.4 rms3.2e-06 |
| actuator_motors collective |  | 32.0Hz x760.1 rms1.9e-05 | 33.5Hz x950.5 rms5.9e-04 | 22.0Hz x277.0 rms2.5e-05 | 18.0Hz x9.9 rms3.1e-06 |
| actuator_motors diffA |  | 33.0Hz x23.9 rms5.6e-06 | 30.0Hz x15.8 rms6.9e-06 | 22.0Hz x126.4 rms1.4e-05 | 24.0Hz x5.3 rms6.2e-07 |
| actuator_motors diffB |  | 33.5Hz x9.3 rms1.4e-05 | 33.5Hz x39.0 rms1.2e-04 | 18.7Hz x1056.0 rms1.6e-04 | 22.0Hz x7.0 rms6.7e-06 |
| actuator_motors diffC |  | 31.5Hz x5.5 rms1.1e-05 | 33.0Hz x27.8 rms7.6e-05 | 18.7Hz x1166.7 rms1.5e-04 | 20.0Hz x4.5 rms6.0e-06 |
| esc rpm collective |  | 33.5Hz x4.7 rms1.7e-01 | 33.5Hz x152.9 rms2.8e+00 | 18.0Hz x15.4 rms4.9e-01 | 18.0Hz x85.2 rms2.1e+00 |
| esc rpm diffA |  | 31.5Hz x5.0 rms1.7e-01 | 35.5Hz x2.0 rms3.2e-01 | 18.7Hz x9.9 rms4.0e-01 | 18.0Hz x2.0 rms8.5e-02 |
| esc rpm diffB |  | 33.5Hz x6.9 rms2.2e-01 | 33.5Hz x6.8 rms5.8e-01 | 18.7Hz x94.4 rms1.2e+00 | 22.0Hz x7.9 rms4.1e-01 |
| esc rpm diffC |  | 30.5Hz x5.1 rms2.0e-01 | 33.0Hz x3.8 rms4.8e-01 | 18.7Hz x82.7 rms1.0e+00 | 18.0Hz x12.9 rms5.8e-01 |
