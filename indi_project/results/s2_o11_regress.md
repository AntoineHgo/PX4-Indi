# O-11 regression check: INDI in mc_rate_control (old) vs module mc_indi_rate_control (new)

Session 38. Old binaries: `build/px4_sitl_default` (v1 path, INDI inside `mc_rate_control`) and
`build/px4_sitl_omega2` (v2 path, measured torque in `control_allocator`). New binary: `build/px4_sitl_o11`
(d2c1f06ad8 + 299a55e2fa). Same params files on both; `run_scenario.py` maps `MC_RATE_CTL_TYPE 1` to
`MC_INDI_EN 1` at boot and `CA_R_W_MAX` to `MC_INDI_W_MAX` on the new binary (282c879f4e). Script
`results/s2_o11_regress/run.sh`, comparison `bench/regress_compare.py`; z = mean difference over its standard error,
|z| < 2 read as run-to-run noise. Tuning set: hover at speed 1, steps and rate pulses at speed 4, seeds 1-3.

Smoke (new binary, v1 hover seed 1): `indi_rate_status` logged, one `vehicle_torque_setpoint` publisher, no
`rate_ctrl_status` (PID not started), `MC_INDI_EN` 0 -> 1 applied at boot.

## v1: frozen INDI (`indi_frz.params`), v1 sim

Against the `indi_frz` reference of `results/s2_recheck_v1/runs/` (old binary): `s2_o11_regress/v1_table.md`.
15/15 runs ok. 22 of 25 metric pairs within |z| < 2; the exceptions are small and favour the new binary:
step_yaw yaw RMS 15.08 vs 15.31 deg (-1.5 %, z -4.0), step_yaw saturation fraction -2.6 % (z -4.4), step_roll
roll-rate RMS -4.4 % (z -2.3).

The reference had flown with 12 parallel simulations (r1f + frz), the new runs with 9, and INDI is known to be
timing-sensitive (session 22: +4 % on H6 between speeds). Same-load control: the old binary re-flown on step_yaw and
step_roll beside the new runs (`run_v1old.sh`, `v1_sameload_table.md`): every metric within |z| < 2 (step_yaw yaw
RMS old 15.31 +- 0.21, new 15.08 +- 0.08, z -1.8; step_roll roll-rate RMS old 0.138 +- 0.007, new 0.133 +- 0.003,
z -1.1). The old binary's own spread on step_yaw is 3x larger under this load than in the reference, so the earlier
|z| > 2 came from the reference's small spread, not from the binary.

**v1 result: the move to the module preserves the frozen v1 behaviour within run-to-run noise.**

## v2: omega2 configuration (`indi_omega2.params`: frozen v1 gains + FAC 0.683 + rotor speed scale 1000 rad/s), v2 sim

Old `build/px4_sitl_omega2` vs new `build/px4_sitl_o11`, flown in the same batch window (`v2_table.md`; v2 sim:
1000 Hz IMU, rotor vibration, 1 % eRPM drops). 30/30 runs ok. `actuator_torque_measured.valid` is 1.0 for
99.7-100 % of each step_roll / rate_step_roll log on both binaries, so the measured-torque path is in use on both.

All metrics within |z| < 2 on hover, step_roll, step_pitch and step_yaw. rate_step_roll is borderline, in the new
binary's favour: roll-rate RMS 0.380 vs 0.385 rad/s (-1.3 %, z -2.3), yaw RMS -5 % (z -2.0), motor-rate effort -10 %
(z -2.2). These three are one scenario's correlated metrics; one borderline scenario out of five, with n = 3 and the
v1 experience that a 1-2 % shift with z ~ -2 vanished under a same-load control, is read as noise. Not chased further:
the deviations listed in `plan/o11_module_spec.md` (torque used one cycle later, as before; non-fresh rotors at trim)
could only show as a small difference, and the difference here is small and favourable.

**v2 result: the measured-torque path computed in the module reproduces the allocator-side placement within
run-to-run noise (borderline on rate_step_roll, 1.3 % better).**

## Conclusion

O-11 is behaviour-preserving for both the frozen v1 configuration and the v2 omega2 configuration. v1 results
(obtained with INDI inside `mc_rate_control`) and v2 results flown with the module are comparable. Not covered by
this check: motor-failure handling (the failed-motor column zeroing was not ported; an offline ESC invalidates the
measured torque and the law falls back to its model): to be seen on V9 (motor_loss_0 on v2) in the v2 validation.
