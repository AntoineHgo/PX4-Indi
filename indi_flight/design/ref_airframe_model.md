# Reference airframe model `quad5in` (stage 1, T3)

Values and their sources: `ref_airframe_data.md`, corrected by `ref_airframe_check.md`; the choices are D-3 in
`DECISIONS.md`. This note records how they map into the simulator and the stock-PID flight check.

## Files
- `indi_flight/sim/models/quad5in_base/model.sdf`: links, inertia, rotor joints. Served through `PX4_GZ_MODELS`
  (D-2); the original model paths stay on `GZ_SIM_RESOURCE_PATH`.
- `indi_flight/sim/models/quad5in/model.sdf`: includes the base, adds the four `MulticopterMotorModel` plugins.
- `ROMFS/px4fmu_common/init.d-posix/airframes/4040_gz_quad5in`: SITL airframe (CA geometry, EC mapping, PID).
- `indi_flight/bench/t3_fly.py`, `t3_analyze.py`: one-off check flight and its analysis (not ported metric code:
  no self-test, no second key; the numbers below are a flyability check, not evidence for a gate).

## Mapping (checked against the SDF, session 3)
| quantity | target | in model |
|---|---|---|
| mass | 0.610 kg | base 0.566 + 4 x rotor 0.011 |
| Ixx, Iyy, Izz | 1.40, 1.50, 2.70 e-3 | base 1.022/1.122/1.944 e-3 + rotor links (parallel axis): 1.40/1.50/2.70 e-3 |
| arm (x, y) | 0.0795 m | rotor joints at (+-0.0795, +-0.0795); `CA_ROTORi_P{X,Y}` the same |
| kT, kQ/kT | 1.5e-6, 0.01267 m | `motorConstant`, `momentConstant`; `CA_ROTORi_KM` +-0.01267 |
| w_max | 2700 rad/s | `maxRotVelocity`, `SIM_GZ_EC_MAX` 2700, `SIM_GZ_EC_MIN` 0 |
| tau up/down | 33 ms | `timeConstantUp/Down` |
| J_rotor | 5e-6 (ASSUMED) | rotor izz 5e-5 with `rotorVelocitySlowdownSim` 10 (D-3); adds 1.8e-4 to static Izz (included above) |
| poles | 14 | `SIM_GZ_ERPM_POL` 14, `SIM_GZ_ESC_FB` 2 |
| thrust map | linear in thrust | `THR_MDL_FAC` 1 (w = w_max u, so thrust ~ u^2 is inverted exactly) |
| hover | w_h ~999 rad/s, u 0.137 | `MPC_THR_HOVER` 0.137 |
| drag | rotorDrag 7.5e-5 | `EKF2_MCOEF` 0.49 = 4 w_h c / m |
Visual/collision motor bodies sit at 0.07 m (cosmetic, no mass).

## Stock-PID check (3 flights, `results/t3_ref_airframe/run{1,2,3}`)
Take-off to 3 m, 20 s hover, offboard steps +1 m z, +2 m x, back, +45 deg yaw, land. All three flew and landed.
- Hover: thrust setpoint 0.1367 (all runs), hover-thrust estimate 0.1367, eRPM telemetry 9537 rpm = 998.7 rad/s
  per motor (model predicts 998.6). Body-rate RMS about mean 0.004 / 0.004 / 0.001 rad/s (no noise model yet).
- Steps (run1/2/3): altitude rise 1.62/1.87/1.60 s, overshoot < 0.4 %; x rise 1.67/1.73/1.66 s, overshoot
  4.9/4.0/3.7 %; yaw rise 0.66 s, overshoot 0.2 %.
- Rate loop (run3, cross-correlation sp to measured): lag 44 ms roll/pitch, 48 ms yaw. The PID gains in the airframe
  file are a hand scaling of the x500 set, not a tuned reference; PID is a reference only (F-5), but a slow PID makes a
  weak comparison. Re-tune with `mc_autotune_attitude_control` before stage 6.

## Open items
1. Rotor reaction torque scaling (D-3 overturn test): fly a yaw step, compare measured yaw acceleration with
   kQ kT sum(+-w^2)/Izz + J_r sum(+-dw/dt)/Izz. Not done.
2. Gyro is logged at 250 Hz in these flights; G1 needs the rate-loop signals at controller rate (logger profile).
3. run1 shows `esc_rpm` 0 in its metrics although parameters are identical to run2/3; probably the analysis script
   changed between runs. Re-run `t3_analyze.py` on run1 to close.
4. Run-to-run spread with identical set-up (altitude rise 1.60-1.87 s) belongs to the stage-1 determinism item.
