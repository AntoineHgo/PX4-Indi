#### indi_flight/results/chatter_probe_s178/p1_vel_lp8/flight.ulg
logged Hz: pos_sp/lpos_sp x,y,z,v 89, lpos (estimate) 89, outer a_c (indi_pos) 89, outer a_f (filt spec.force) 89, outer t_c/t_c_applied 89, att_sp q_d,thrust_body 89, rates_sp (267Hz) 267, vehicle_acceleration 267, gyro (angular_velocity) 799, inner nu/alpha_f/tau_f 799, inner dtau/rates_sp_applied 799, torque_setpoint 799, thrust_setpoint 799, torque_measured 799, actuator_motors 799
| signal | comp | ctl(18-28) | L1(38-52) | L2d(62-66.5) | L2g(69.5-72) |
|---|---|---|---|---|---|
| pos_sp/lpos_sp x,y,z,v | thrust[0] | 31.1Hz x1.1 rms9.4e-07 | 33.1Hz x1817.3 rms8.7e-04 | 18.7Hz x18621.3 rms4.8e-04 | 18.2Hz x0.0 rms0.0e+00 |
| lpos (estimate) | vy | 33.6Hz x1.3 rms1.2e-05 | 36.2Hz x1.2 rms5.2e-05 | 18.7Hz x20458.6 rms3.7e-03 | 18.2Hz x63.5 rms3.1e-05 |
| outer a_c (indi_pos) | a_c[1] | 30.1Hz x1.3 rms2.8e-05 | 33.1Hz x465.9 rms7.8e-02 | 18.7Hz x16712.7 rms1.1e-02 | n/a |
| outer a_f (filt spec.force) | a_f[0] | 31.6Hz x1.3 rms7.8e-05 | 30.1Hz x1.4 rms1.9e-04 | 18.7Hz x33539.1 rms2.5e-02 | n/a |
| outer t_c/t_c_applied | t_c[0] | 31.6Hz x1.1 rms9.7e-05 | 33.1Hz x1832.4 rms7.8e-02 | 18.7Hz x25791.3 rms3.5e-02 | n/a |
| att_sp q_d,thrust_body | q_d[1] | 30.1Hz x1.0 rms4.8e-06 | 33.1Hz x1761.0 rms2.6e-03 | 18.7Hz x24856.5 rms1.7e-03 | 18.2Hz x0.0 rms0.0e+00 |
| rates_sp (267Hz) | roll | 36.0Hz x1.0 rms1.4e-05 | 33.5Hz x93.1 rms1.4e-03 | 18.7Hz x13837.2 rms4.0e-03 | 19.0Hz x9.6 rms8.7e-06 |
| vehicle_acceleration | xyz[0] | 30.0Hz x6.5 rms8.2e-04 | 35.5Hz x3.5 rms7.8e-04 | 18.0Hz x2.7 rms1.7e-03 | 18.0Hz x519.1 rms4.3e-03 |
| gyro (angular_velocity) | xyz[1] | 33.5Hz x11.1 rms1.6e-04 | 33.5Hz x14.7 rms2.1e-04 | 18.7Hz x185.9 rms6.7e-04 | 18.0Hz x11.8 rms1.5e-04 |
| inner nu/alpha_f/tau_f | torque_filtered[1] | 33.5Hz x63.9 rms3.5e-06 | 33.5Hz x76.7 rms1.1e-05 | 18.7Hz x4159.4 rms3.2e-05 | 18.0Hz x0.0 rms0.0e+00 |
| inner dtau/rates_sp_applied | torque_increment[0] | 33.0Hz x6.1 rms1.6e-05 | 33.5Hz x40.0 rms1.3e-04 | 18.7Hz x739.1 rms2.1e-04 | 24.0Hz x3.6 rms7.3e-06 |
| torque_setpoint | xyz[0] | 33.0Hz x6.2 rms1.6e-05 | 33.5Hz x40.6 rms1.3e-04 | 18.7Hz x546.9 rms1.8e-04 | 24.0Hz x3.5 rms7.3e-06 |
| thrust_setpoint | xyz[2] | 32.0Hz x25.8 rms5.3e-06 | 33.5Hz x1858.0 rms5.8e-04 | 22.0Hz x130.5 rms2.5e-05 | 18.0Hz x10.8 rms2.8e-06 |
| torque_measured | torque[1] | 33.5Hz x4.6 rms8.7e-06 | 33.5Hz x8.5 rms2.8e-05 | 18.7Hz x117.9 rms4.7e-05 | 18.0Hz x14.9 rms5.9e-07 |
| actuator_motors collective |  | 32.0Hz x25.9 rms5.3e-06 | 33.5Hz x1857.7 rms5.8e-04 | 22.0Hz x127.3 rms2.5e-05 | 18.0Hz x10.8 rms2.8e-06 |
| actuator_motors diffA |  | 34.0Hz x26.7 rms5.4e-06 | 30.0Hz x26.5 rms8.4e-06 | 21.3Hz x82.8 rms1.2e-05 | 20.0Hz x4.1 rms5.9e-07 |
| actuator_motors diffB |  | 33.5Hz x7.6 rms1.4e-05 | 33.5Hz x60.9 rms1.3e-04 | 18.7Hz x436.6 rms1.3e-04 | 22.0Hz x6.3 rms6.5e-06 |
| actuator_motors diffC |  | 33.0Hz x6.2 rms1.1e-05 | 33.5Hz x40.6 rms9.0e-05 | 18.7Hz x552.0 rms1.3e-04 | 24.0Hz x3.6 rms5.2e-06 |
| esc rpm collective |  | 32.0Hz x4.2 rms2.0e-01 | 33.5Hz x178.4 rms2.7e+00 | 18.0Hz x14.1 rms4.7e-01 | 18.0Hz x65.4 rms2.2e+00 |
| esc rpm diffA |  | 36.5Hz x5.0 rms2.2e-01 | 30.5Hz x2.7 rms3.6e-01 | 19.3Hz x9.5 rms3.6e-01 | 20.0Hz x1.9 rms7.3e-03 |
| esc rpm diffB |  | 33.5Hz x4.6 rms2.1e-01 | 33.5Hz x9.1 rms6.8e-01 | 18.7Hz x115.8 rms1.2e+00 | 18.0Hz x17.1 rms1.4e-01 |
| esc rpm diffC |  | 30.5Hz x3.5 rms1.9e-01 | 33.0Hz x5.6 rms5.4e-01 | 18.7Hz x96.5 rms1.1e+00 | 22.0Hz x42.7 rms2.3e-01 |
