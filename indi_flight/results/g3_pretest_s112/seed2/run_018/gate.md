# Pre-test gate: `seed2/run_018/flight.ulg`

- window: [47.008, 77.007) s since boot, first airborne + 15.0 s
- samples: angular velocity 24000, motors 24000, allocator 6000
- rate RMS x/y/z [rad/s]: 0.1127 / 0.1408 / 0.1163 (limit 0.02)
- motor pin fraction: 0 (limit 0.01)
- torque setpoint achieved fraction: 1 (limit 0.9)

FAIL: rate RMS axis 0 0.1127 >= 0.02; rate RMS axis 1 0.1408 >= 0.02; rate RMS axis 2 0.1163 >= 0.02
