# S73: A-33 closing test, rate-loop blend on under one weak motor

Firmware: build of 41d44d461a (S72 D-GAP, unchanged). Scenario `s5_loss08` (one motor at 0.8 thrust in position
hold), seed 1, `--sim v2 --speed 4`, two flights in parallel (instances 0/1). Params = `stage5_s70/gap.params` +
`MC_INDI_ACT_BLD` (rate-loop complementary blend time constant; firmware default 0 = measured torque only, and it was
not set in the S72 flights).

Analysis: `s5_gap_check.py RUN` (dz, positive = below hold), `bench/a33_tilt_split.py RUN...` (last 10 s:
attitude setpoint vs actual tilt, motor commands, rate setpoint vs rate). `a33_tilt_split.py` was written in S73
without reading T162's code and reproduces T162's S72 numbers (`stage5_s72/a33_split.md`): loss08_indi tilt_sp 10.39
deg, actual 0.14, sp-vs-actual 10.41 (T162: 10.42 / 0.14 / 10.41), so it is a second key on the split.

| run | ACT_BLD (s) | tilt sp / actual (deg) | sp-vs-actual (deg) | rate_sp r/p (rad/s) | dz ev+10-20 / last10 (m) | max abs dz after event (m) | motors 0..3 |
|---|---|---|---|---|---|---|---|
| S72 loss08_indi | 0 | 10.39 / 0.14 | 10.41 | +1.062 / +0.990 | -0.036 / -0.056 | 0.075 | .137 .137 .171 .137 |
| loss08_bld0.3 | 0.3 | 0.13 / 0.13 | 0.05 | 0.000 / 0.000 | +0.026 / +0.037 | 0.107 | .137 .137 .171 .137 |
| loss08_bld1.0 | 1.0 | 0.18 / 0.18 | 0.06 | 0.000 / 0.000 | +0.020 / +0.024 | 0.046 | .137 .137 .171 .137 |

Reading: with the blend off, the rate loop has no integral action against the weak motor (lesson 9). All rotor speeds
are equal (eRPM sees the fault: closing test (a), the fault scales command to omega and telemetry sees it), the
measured torque is zero, so the
asymmetric motor command needs a standing rate error (about 1 rad/s), hence a standing attitude error of 10.4 deg; the
outer loop then winds its xy gap state to -1.3 m/s2 and loses g(1 - cos 10.4 deg) vertically. With the blend on, the
standing rate and attitude errors vanish and the same motor asymmetry is held with zero error (closing test (b)).
Closing test (c) (stock mc_pos + INDI rate) not flown: (a) and (b) explain the anomaly completely.

Open from this: the firmware default 0 is not a validated configuration (lesson 12). The 0.3 s blend shows a larger
post-event vertical transient (0.107 m vs 0.046 m), one seed each, not yet explained. See D-RATE-BLD in DECISIONS.md.
Raw logs (flight.ulg, gz.log, px4.log) stay untracked.
