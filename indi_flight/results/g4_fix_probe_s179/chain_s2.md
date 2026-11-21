#### indi_flight/results/g4_fix_probe_s179/f1_lpf5_s2/flight.ulg
logged Hz: pos_sp/lpos_sp x,y,z,v 89, lpos (estimate) 89, outer a_c (indi_pos) 89, outer a_f (filt spec.force) 89, outer t_c/t_c_applied 89, att_sp q_d,thrust_body 89, rates_sp (267Hz) 267, vehicle_acceleration 267, gyro (angular_velocity) 799, inner nu/alpha_f/tau_f 799, inner dtau/rates_sp_applied 799, torque_setpoint 799, thrust_setpoint 799, torque_measured 799, actuator_motors 799
| signal | comp | ctl(18-28) | L1(38-52) | L2d(62-66.5) | L2g(69.5-72) |
|---|---|---|---|---|---|
| pos_sp/lpos_sp x,y,z,v | thrust[0] | 30.1Hz x1.8 rms2.6e-06 | 33.1Hz x321.1 rms8.5e-04 | 18.7Hz x29510.7 rms5.0e-04 | 22.2Hz x79.4 rms3.6e-14 |
| lpos (estimate) | vx | 30.1Hz x1.8 rms2.0e-05 | 32.6Hz x1.7 rms7.3e-05 | 18.7Hz x32196.7 rms4.0e-03 | 18.2Hz x38.2 rms4.1e-05 |
| outer a_c (indi_pos) | a_c[0] | 30.1Hz x1.8 rms1.8e-04 | 33.1Hz x327.6 rms6.2e-02 | 18.7Hz x28025.5 rms3.5e-02 | n/a |
| outer a_f (filt spec.force) | a_f[0] | 30.6Hz x1.9 rms3.3e-05 | 34.1Hz x1.2 rms1.5e-04 | 18.7Hz x29240.9 rms6.4e-03 | n/a |
| outer t_c/t_c_applied | t_c[0] | 30.1Hz x1.8 rms1.8e-04 | 33.1Hz x324.8 rms6.2e-02 | 18.7Hz x29503.2 rms3.6e-02 | n/a |
| att_sp q_d,thrust_body | q_d[2] | 30.1Hz x1.4 rms8.1e-06 | 33.1Hz x137.4 rms2.2e-03 | 18.7Hz x27091.4 rms1.8e-03 | 22.2Hz x38.5 rms1.8e-11 |
| rates_sp (267Hz) | roll | 31.5Hz x1.8 rms1.9e-05 | 33.5Hz x65.7 rms1.4e-03 | 18.7Hz x23547.1 rms4.0e-03 | 20.1Hz x13.5 rms9.0e-06 |
| vehicle_acceleration | xyz[1] | 30.0Hz x2.0 rms1.3e-03 | 30.0Hz x2.9 rms7.6e-04 | 20.1Hz x4.1 rms1.5e-03 | 18.0Hz x550.2 rms4.8e-03 |
| gyro (angular_velocity) | xyz[1] | 33.5Hz x12.3 rms1.7e-04 | 33.5Hz x18.6 rms2.4e-04 | 18.7Hz x257.0 rms8.3e-04 | 21.0Hz x7.6 rms1.3e-04 |
| inner nu/alpha_f/tau_f | nu[0] | 30.0Hz x6.7 rms3.2e-03 | 33.5Hz x76.6 rms5.5e-02 | 18.7Hz x6241.9 rms9.5e-02 | 20.0Hz x6.7 rms2.7e-03 |
| inner dtau/rates_sp_applied | torque_increment[0] | 33.0Hz x6.5 rms1.6e-05 | 33.5Hz x57.0 rms1.3e-04 | 18.7Hz x1151.7 rms2.1e-04 | 24.0Hz x4.2 rms7.6e-06 |
| torque_setpoint | xyz[0] | 31.5Hz x6.3 rms1.7e-05 | 33.5Hz x56.7 rms1.3e-04 | 18.7Hz x940.1 rms1.9e-04 | 24.0Hz x4.1 rms7.6e-06 |
| thrust_setpoint | xyz[2] | 32.0Hz x1088.0 rms2.0e-05 | 33.5Hz x984.5 rms5.9e-04 | 22.0Hz x46.4 rms2.4e-05 | 18.0Hz x10.8 rms2.9e-06 |
| torque_measured | torque[1] | 35.5Hz x4.0 rms6.5e-06 | 33.5Hz x10.0 rms3.0e-05 | 18.7Hz x72.0 rms4.0e-05 | 19.0Hz x3.6 rms9.6e-07 |
| actuator_motors collective |  | 32.0Hz x1080.7 rms2.0e-05 | 33.5Hz x981.6 rms5.9e-04 | 22.0Hz x47.6 rms2.4e-05 | 18.0Hz x10.8 rms2.9e-06 |
| actuator_motors diffA |  | 30.5Hz x19.8 rms5.2e-06 | 31.0Hz x23.0 rms6.5e-06 | 18.7Hz x188.6 rms1.5e-05 | 24.0Hz x4.9 rms5.9e-07 |
| actuator_motors diffB |  | 33.5Hz x9.8 rms1.5e-05 | 33.5Hz x78.6 rms1.4e-04 | 18.7Hz x915.5 rms1.5e-04 | 21.0Hz x4.9 rms5.6e-06 |
| actuator_motors diffC |  | 31.5Hz x6.2 rms1.2e-05 | 33.5Hz x57.0 rms9.1e-05 | 18.7Hz x948.3 rms1.4e-04 | 20.0Hz x4.0 rms5.3e-06 |
| esc rpm collective |  | 32.0Hz x4.6 rms1.8e-01 | 33.5Hz x161.5 rms2.7e+00 | 18.7Hz x9.0 rms3.8e-01 | 18.0Hz x58.9 rms2.1e+00 |
| esc rpm diffA |  | 36.0Hz x4.5 rms1.7e-01 | 31.0Hz x2.3 rms3.1e-01 | 20.7Hz x3.4 rms2.3e-01 | 21.0Hz x2.4 rms5.8e-02 |
| esc rpm diffB |  | 35.5Hz x4.2 rms1.6e-01 | 33.5Hz x10.4 rms7.1e-01 | 18.7Hz x73.0 rms1.0e+00 | 19.0Hz x2.8 rms2.0e-01 |
| esc rpm diffC |  | 30.5Hz x5.7 rms2.0e-01 | 33.0Hz x4.2 rms4.8e-01 | 18.7Hz x63.9 rms8.2e-01 | 24.0Hz x11.6 rms3.3e-01 |
