# Pre-test gate: `indi_flight/results/g2_freeze_s160/yaw400_s1/s1/flight.ulg`

- window: [35.609, 50.609) s since boot, first airborne + 4.0 s
- samples: angular velocity 2980, motors 2980, allocator 1485
- rate RMS x/y/z [rad/s]: 0.7364 / 0.743 / 0.02982 (limit 0.02)
- motor pin fraction: 0.009396 (limit 0.01)
- torque setpoint achieved fraction: 0.9906 (limit 0.9)

FAIL: rate RMS axis 0 0.7364 >= 0.02; rate RMS axis 1 0.743 >= 0.02; rate RMS axis 2 0.02982 >= 0.02
