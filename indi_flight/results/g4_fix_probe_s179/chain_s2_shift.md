#### indi_flight/results/g4_fix_probe_s179/f1_lpf5_s2/flight.ulg
logged Hz: pos_sp/lpos_sp x,y,z,v 89, lpos (estimate) 89, outer a_c (indi_pos) 89, outer a_f (filt spec.force) 89, outer t_c/t_c_applied 89, att_sp q_d,thrust_body 89, rates_sp (267Hz) 267, vehicle_acceleration 267, gyro (angular_velocity) 799, inner nu/alpha_f/tau_f 799, inner dtau/rates_sp_applied 799, torque_setpoint 799, thrust_setpoint 799, torque_measured 799, actuator_motors 799
| signal | comp | ctl(18-28) | L1(38-52) | L2d(62-66.5) | L2g(69.5-72) |
|---|---|---|---|---|---|
| pos_sp/lpos_sp x,y,z,v | acceleration[0] | 30.1Hz x1.8 rms1.8e-04 | 33.1Hz x327.6 rms6.2e-02 | 18.7Hz x30040.7 rms3.5e-02 | 18.2Hz x0.0 rms0.0e+00 |
| lpos (estimate) | ax | 30.1Hz x1.5 rms1.8e-03 | 32.6Hz x1.1 rms4.1e-03 | 18.7Hz x39600.0 rms4.4e-01 | 18.2Hz x16.5 rms4.2e-03 |
| outer a_c (indi_pos) | a_c[0] | 30.1Hz x1.8 rms1.8e-04 | 33.1Hz x327.6 rms6.2e-02 | 18.7Hz x30040.7 rms3.5e-02 | n/a |
| outer a_f (filt spec.force) | a_f[0] | 30.6Hz x1.9 rms3.3e-05 | 34.1Hz x1.2 rms1.5e-04 | 18.7Hz x28947.5 rms6.4e-03 | n/a |
| outer t_c/t_c_applied | t_c[0] | 30.1Hz x1.8 rms1.8e-04 | 33.1Hz x324.8 rms6.2e-02 | 18.7Hz x28596.6 rms3.6e-02 | n/a |
| att_sp q_d,thrust_body | q_d[2] | 30.1Hz x1.4 rms8.1e-06 | 33.1Hz x137.4 rms2.2e-03 | 18.7Hz x29721.1 rms1.8e-03 | 22.2Hz x38.5 rms1.8e-11 |
| rates_sp (267Hz) | roll | 31.5Hz x1.8 rms1.9e-05 | 33.5Hz x65.7 rms1.4e-03 | 18.7Hz x24218.7 rms4.0e-03 | 20.1Hz x13.5 rms9.0e-06 |
| vehicle_acceleration | xyz[1] | 30.0Hz x2.0 rms1.3e-03 | 30.0Hz x2.9 rms7.6e-04 | 20.1Hz x4.8 rms1.4e-03 | 18.0Hz x550.2 rms4.8e-03 |
| gyro (angular_velocity) | xyz[1] | 33.5Hz x12.3 rms1.7e-04 | 33.5Hz x18.6 rms2.4e-04 | 18.7Hz x280.7 rms8.1e-04 | 21.0Hz x7.6 rms1.3e-04 |
| inner nu/alpha_f/tau_f | nu[1] | 33.5Hz x7.6 rms3.5e-03 | 33.5Hz x96.8 rms7.8e-02 | 18.7Hz x6176.4 rms9.7e-02 | 21.0Hz x7.5 rms2.6e-03 |
| inner dtau/rates_sp_applied | torque_increment[1] | 33.5Hz x9.0 rms2.0e-05 | 33.5Hz x80.9 rms1.9e-04 | 18.7Hz x1266.3 rms2.4e-04 | 21.0Hz x4.7 rms7.8e-06 |
| torque_setpoint | xyz[1] | 33.5Hz x9.8 rms2.1e-05 | 33.5Hz x81.9 rms1.9e-04 | 18.7Hz x1046.7 rms2.2e-04 | 21.0Hz x4.6 rms7.8e-06 |
| thrust_setpoint | xyz[2] | 32.0Hz x1088.0 rms2.0e-05 | 33.5Hz x984.5 rms5.9e-04 | 22.0Hz x35.7 rms2.4e-05 | 18.0Hz x10.8 rms2.9e-06 |
| torque_measured | torque[1] | 35.5Hz x4.0 rms6.5e-06 | 33.5Hz x10.0 rms3.0e-05 | 18.7Hz x68.0 rms3.8e-05 | 19.0Hz x3.6 rms9.6e-07 |
| actuator_motors collective |  | 32.0Hz x1080.7 rms2.0e-05 | 33.5Hz x981.6 rms5.9e-04 | 22.0Hz x36.9 rms2.4e-05 | 18.0Hz x10.8 rms2.9e-06 |
| actuator_motors diffA |  | 30.5Hz x19.8 rms5.2e-06 | 31.0Hz x23.0 rms6.5e-06 | 19.3Hz x141.3 rms1.5e-05 | 24.0Hz x4.9 rms5.9e-07 |
| actuator_motors diffB |  | 33.5Hz x9.8 rms1.5e-05 | 33.5Hz x78.6 rms1.4e-04 | 18.7Hz x1039.0 rms1.5e-04 | 21.0Hz x4.9 rms5.6e-06 |
| actuator_motors diffC |  | 31.5Hz x6.2 rms1.2e-05 | 33.5Hz x57.0 rms9.1e-05 | 18.7Hz x815.1 rms1.4e-04 | 20.0Hz x4.0 rms5.3e-06 |
| esc rpm collective |  | 32.0Hz x4.6 rms1.8e-01 | 33.5Hz x161.5 rms2.7e+00 | 23.3Hz x8.2 rms3.6e-01 | 18.0Hz x58.9 rms2.1e+00 |
| esc rpm diffA |  | 36.0Hz x4.5 rms1.7e-01 | 31.0Hz x2.3 rms3.1e-01 | 20.7Hz x4.7 rms2.6e-01 | 21.0Hz x2.4 rms5.8e-02 |
| esc rpm diffB |  | 35.5Hz x4.2 rms1.6e-01 | 33.5Hz x10.4 rms7.1e-01 | 18.7Hz x70.3 rms9.4e-01 | 19.0Hz x2.8 rms2.0e-01 |
| esc rpm diffC |  | 30.5Hz x5.7 rms2.0e-01 | 33.0Hz x4.2 rms4.8e-01 | 18.7Hz x60.8 rms8.1e-01 | 24.0Hz x11.6 rms3.3e-01 |
