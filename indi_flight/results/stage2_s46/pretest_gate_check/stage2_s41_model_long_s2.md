# Pre-test gate: `results/stage2_s41/model_long_s2/flight.ulg`

- window: [47.017, 77.017) s since boot, first airborne + 15.0 s
- samples: angular velocity 23991, motors 23993, allocator 5992
- rate RMS x/y/z [rad/s]: 0.2775 / 1.187 / 0.07298 (limit 0.02)
- motor pin fraction: 0.8925 (limit 0.01)
- torque setpoint achieved fraction: 0.1123 (limit 0.9)

FAIL: rate RMS axis 0 0.2775 >= 0.02; rate RMS axis 1 1.187 >= 0.02; rate RMS axis 2 0.07298 >= 0.02; motor pin 0.8925 >= 0.01; torque achieved 0.1123 <= 0.9
