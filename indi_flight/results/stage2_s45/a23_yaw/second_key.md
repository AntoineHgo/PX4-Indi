# Second-key check: S45 A-23 yaw flight (indi_g1y)

Log: `/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/stage2_s45/a23_yaw/indi_g1y/flight.ulg`
Window: 52.0 s to 82.0 s since boot (topic timestamp / 1e6)

Self-test: RMS of unit sine = 0.707105 (PASS, tol 1e-3)

## 1. vehicle_angular_velocity.xyz (demeaned RMS, rad/s)

- samples in window: 24000
- median sample interval: 1.250 ms (800.0 Hz)
- RMS roll  xyz[0]: 0.006769 rad/s
- RMS pitch xyz[1]: 0.005602 rad/s
- RMS yaw   xyz[2]: 0.001668 rad/s
- pass criterion pitch RMS < 0.02 rad/s: PASS

## 2. actuator_motors.control[0..3]

- samples in window: 24000

| motor | frac < 0.005 | mean | std | pass (<1%) |
|---|---|---|---|---|
| 0 | 0.0000% | 0.1367 | 0.0009 | PASS |
| 1 | 0.0000% | 0.1367 | 0.0009 | PASS |
| 2 | 0.0000% | 0.1367 | 0.0009 | PASS |
| 3 | 0.0000% | 0.1367 | 0.0009 | PASS |

- pass criterion every motor < 0.005 on < 1% of samples: PASS

## 3. control_allocator_status.torque_setpoint_achieved

- samples in window: 5989
- fraction true: 100.0000%

