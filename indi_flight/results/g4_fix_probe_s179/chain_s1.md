#### indi_flight/results/g4_fix_probe_s179/f1_lpf5_s1/flight.ulg
logged Hz: pos_sp/lpos_sp x,y,z,v 89, lpos (estimate) 89, outer a_c (indi_pos) 89, outer a_f (filt spec.force) 89, outer t_c/t_c_applied 89, att_sp q_d,thrust_body 89, rates_sp (267Hz) 267, vehicle_acceleration 267, gyro (angular_velocity) 800, inner nu/alpha_f/tau_f 800, inner dtau/rates_sp_applied 800, torque_setpoint 800, thrust_setpoint 800, torque_measured 800, actuator_motors 800
| signal | comp | ctl(18-28) | L1(38-52) | L2d(62-66.5) | L2g(69.5-72) |
|---|---|---|---|---|---|
| pos_sp/lpos_sp x,y,z,v | thrust[1] | 30.1Hz x1.2 rms1.1e-06 | 33.1Hz x163.1 rms4.5e-04 | 18.7Hz x760255.3 rms4.2e-04 | 22.2Hz x33.0 rms2.6e-14 |
| lpos (estimate) | vy | 30.1Hz x1.6 rms6.1e-06 | 31.6Hz x1.4 rms3.9e-05 | 18.7Hz x1234487.0 rms3.4e-03 | 18.2Hz x33.1 rms2.0e-05 |
| outer a_c (indi_pos) | a_c[1] | 30.1Hz x1.9 rms9.5e-05 | 33.1Hz x230.4 rms6.7e-02 | 18.7Hz x256619.3 rms3.5e-02 | 18.2Hz x0.0 rms0.0e+00 |
| outer a_f (filt spec.force) | a_f[1] | 32.6Hz x1.1 rms1.9e-05 | 35.2Hz x0.9 rms4.9e-04 | 18.7Hz x425738.3 rms6.3e-03 | 18.2Hz x3.6 rms1.2e-07 |
| outer t_c/t_c_applied | t_c[1] | 30.1Hz x1.9 rms8.3e-05 | 33.1Hz x234.1 rms6.7e-02 | 18.7Hz x271929.4 rms3.5e-02 | 22.2Hz x19.7 rms2.9e-12 |
| att_sp q_d,thrust_body | q_d[1] | 32.1Hz x1.2 rms4.1e-06 | 33.1Hz x110.8 rms1.2e-03 | 18.7Hz x1321379.4 rms1.5e-03 | 22.2Hz x32.3 rms5.5e-12 |
| rates_sp (267Hz) | pitch | 33.5Hz x1.7 rms1.5e-05 | 33.5Hz x43.1 rms1.3e-03 | 18.7Hz x417565.3 rms4.0e-03 | 18.0Hz x8.8 rms7.3e-06 |
| vehicle_acceleration | xyz[1] | 34.0Hz x6.1 rms9.0e-04 | 32.5Hz x3.7 rms7.8e-04 | 20.7Hz x18.6 rms1.1e-03 | 18.0Hz x190.6 rms2.7e-03 |
| gyro (angular_velocity) | xyz[0] | 30.0Hz x10.4 rms1.6e-04 | 32.5Hz x11.0 rms1.8e-04 | 18.7Hz x230.9 rms7.4e-04 | 19.0Hz x9.3 rms1.5e-04 |
| inner nu/alpha_f/tau_f | nu[0] | 30.0Hz x7.3 rms3.4e-03 | 33.5Hz x51.8 rms5.1e-02 | 18.7Hz x6887.6 rms9.5e-02 | 19.0Hz x9.2 rms3.2e-03 |
| inner dtau/rates_sp_applied | torque_increment[0] | 30.0Hz x7.5 rms1.7e-05 | 33.5Hz x33.1 rms1.2e-04 | 18.7Hz x1150.3 rms2.1e-04 | 19.0Hz x5.4 rms8.6e-06 |
| torque_setpoint | xyz[0] | 30.0Hz x7.2 rms1.7e-05 | 33.5Hz x31.3 rms1.2e-04 | 18.7Hz x874.2 rms1.9e-04 | 19.0Hz x5.5 rms8.6e-06 |
| thrust_setpoint | xyz[2] | 32.0Hz x914.9 rms2.0e-05 | 33.5Hz x1383.0 rms6.1e-04 | 22.0Hz x979.5 rms2.5e-05 | 18.0Hz x10.7 rms2.5e-06 |
| torque_measured | torque[0] | 32.0Hz x7.1 rms8.5e-06 | 33.5Hz x3.8 rms1.9e-05 | 18.7Hz x116.0 rms4.4e-05 | 19.0Hz x15.9 rms2.3e-06 |
| actuator_motors collective |  | 32.0Hz x912.3 rms2.0e-05 | 33.5Hz x1354.4 rms6.1e-04 | 22.0Hz x1000.3 rms2.5e-05 | 18.0Hz x11.3 rms2.4e-06 |
| actuator_motors diffA |  | 30.0Hz x25.6 rms5.8e-06 | 30.0Hz x15.5 rms6.9e-06 | 20.7Hz x87.5 rms1.2e-05 | 24.0Hz x5.5 rms6.0e-07 |
| actuator_motors diffB |  | 33.5Hz x8.3 rms1.3e-05 | 33.5Hz x58.7 rms1.3e-04 | 18.7Hz x689.6 rms1.3e-04 | 23.0Hz x4.8 rms5.6e-06 |
| actuator_motors diffC |  | 30.0Hz x7.2 rms1.2e-05 | 33.5Hz x32.1 rms8.2e-05 | 18.7Hz x880.4 rms1.3e-04 | 19.0Hz x5.9 rms6.0e-06 |
| esc rpm collective |  | 32.0Hz x3.7 rms1.4e-01 | 33.5Hz x173.9 rms2.9e+00 | 22.0Hz x13.1 rms3.5e-01 | 18.0Hz x40.5 rms1.9e+00 |
| esc rpm diffA |  | 35.0Hz x5.9 rms1.6e-01 | 30.0Hz x1.9 rms3.3e-01 | 21.3Hz x10.7 rms3.4e-01 | 18.0Hz x2.7 rms6.9e-02 |
| esc rpm diffB |  | 30.5Hz x4.5 rms1.7e-01 | 33.5Hz x9.3 rms7.5e-01 | 18.7Hz x106.9 rms1.0e+00 | 23.0Hz x13.2 rms5.5e-01 |
| esc rpm diffC |  | 32.0Hz x7.0 rms2.1e-01 | 33.5Hz x3.7 rms4.5e-01 | 18.7Hz x115.6 rms1.1e+00 | 19.0Hz x16.2 rms5.5e-01 |
