# Pre-test gate: `results/stage2_s44/a23_test/indi_g1derived/flight.ulg`

- window: [47.014, 77.014) s since boot, first airborne + 15.0 s
- samples: angular velocity 23986, motors 23987, allocator 5987
- rate RMS x/y/z [rad/s]: 0.04442 / 0.03637 / 0.4166 (limit 0.02)
- motor pin fraction: 0.9283 (limit 0.01)
- torque setpoint achieved fraction: 0.07333 (limit 0.9)

FAIL: rate RMS axis 0 0.04442 >= 0.02; rate RMS axis 1 0.03637 >= 0.02; rate RMS axis 2 0.4166 >= 0.02; motor pin 0.9283 >= 0.01; torque achieved 0.07333 <= 0.9
