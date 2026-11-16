# Pre-test gate: `indi_flight/results/stage2_s47/roll_m3a/model_s1/flight.ulg`

- window: [47.019, 77.019) s since boot, first airborne + 15.0 s
- samples: angular velocity 23997, motors 23997, allocator 5930
- rate RMS x/y/z [rad/s]: 1.148 / 0.1449 / 0.2261 (limit 0.02)
- motor pin fraction: 0.2609 (limit 0.01)
- torque setpoint achieved fraction: 0.7551 (limit 0.9)

FAIL: rate RMS axis 0 1.148 >= 0.02; rate RMS axis 1 0.1449 >= 0.02; rate RMS axis 2 0.2261 >= 0.02; motor pin 0.2609 >= 0.01; torque achieved 0.7551 <= 0.9
