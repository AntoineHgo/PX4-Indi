# Pre-test gate: `seed1/run_003/flight.ulg`

- window: [47.019, 77.019) s since boot, first airborne + 15.0 s
- samples: angular velocity 24000, motors 24000, allocator 6000
- rate RMS x/y/z [rad/s]: 0.03338 / 0.08221 / 0.0208 (limit 0.02)
- motor pin fraction: 0 (limit 0.01)
- torque setpoint achieved fraction: 1 (limit 0.9)

FAIL: rate RMS axis 0 0.03338 >= 0.02; rate RMS axis 1 0.08221 >= 0.02; rate RMS axis 2 0.0208 >= 0.02
