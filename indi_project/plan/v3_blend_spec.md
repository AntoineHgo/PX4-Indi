# Implementation spec: D-v3-blend (session 43)

Design and motivation: `plan/v3_actuator_blend.md`. This file is the brief for the implementing agent; its log goes to
`plan/impl_log_v3_blend.md` (write it after every step).

## Change (library `src/lib/indi_rate_control`)

In `IndiRateControl::update()`, step 5c currently selects `t_f = _meas_in_use ? t_f_meas : t_f_model`. Replace the
measured branch by a complementary blend, per axis:

    blend   <- blend + alpha * ((t_f_model - t_f_meas) - blend),   alpha = dt / (Tb + dt)
    t_f      = t_f_meas + blend                                   (when the measurement is in use)

- New setter `setActuatorBlendTimeConstant(float tb_s)`: Tb in seconds. Tb <= 0 or non-finite disables the blend
  (store 0): then `t_f = t_f_meas` exactly as today (v2 behaviour, bit-identical outputs). Clamp to <= 10 s.
- New member `matrix::Vector3f _blend` (statically allocated). Zeroed by `reset()`.
- While the measurement is NOT in use, or the blend is disabled, or `landed`: set `_blend = t_f_model - t_f_meas`
  every cycle (tracking), so that enabling the blend, switching model -> measurement, or taking off is bumpless.
- Clamp `_blend` to [-2, 2] per axis (both torques are within [-1, 1]); if it is non-finite, set it to the current
  difference (or zero if that is non-finite too).
- The yaw low pass (step 6b) and the G2 term then act on the blended t_f as they do on t_f today; no other change.
- Update the header comment block (the "Measured torque path" paragraph) to describe the blend in two or three lines,
  and add a getter `getActuatorBlend()` returning `_blend` for logging if useful (optional, no message change).
- dt: use the same dt `update()` already validates; no extra state.

## Module `src/modules/mc_indi_rate_control`

- New parameter `MC_INDI_ACT_BLD` in `mc_indi_rate_control_params.yaml`: float, unit s, default 0.0 (disabled, v2),
  min 0.0, max 10.0, decimal 2, increment 0.05. Description: time constant of the complementary blend between the
  measured (high frequency) and modelled (low frequency) actuator state; restores the integral action of the model
  state against a steady command/output gap; 0 disables (measured state only). Follow the style of the existing
  MC_INDI_* entries in that file.
- Read it with the other parameters (`DEFINE_PARAMETERS` / `updateParams` path) and pass it to the library setter.

## Unit tests (`src/lib/indi_rate_control/indi_rate_control_test.cpp`, gtest, same style as the existing tests)

1. Blend disabled (Tb = 0, also NaN and negative): outputs identical to a controller that never had the setter
   called, over a few hundred cycles with a valid measurement that differs from the model.
2. Steady gap: measurement valid and equal to 0.7 x the model torque on roll (constant command input so the model
   settles). With Tb = 0.3 s and dt = 1/1000 (or the dt used by existing tests), after >= 5 Tb of cycles the fed-back
   torque (`getFilteredTorque()` or whatever the existing tests use for t_f) is within 1 % of the model value; with
   Tb = 0 it equals the measured value.
3. High-frequency pass-through: blend enabled and settled, then a step in the measured torque only: the change in t_f
   over the next few cycles follows the measured path (>= 90 % of the measured-only response after the same cycles).
4. Bumpless switch: measurement invalid for a while, then valid for kMeasValidCycles: no jump in t_f larger than the
   change of t_f_model + 1e-4 at the switch cycle, with the blend enabled.
5. Landed: with landed = true and a gap, `_blend` tracks the difference (no accumulation): after landing -> airborne,
   the first airborne t_f equals the value without blend memory (t_f_model).
Keep the existing tests unchanged and passing.

## Build, format, commit

- Tests: `indi_project/docker/run.sh -t 1150 'nice -n 19 make tests TESTFILTER=indi'` (builds in `build/px4_sitl_test`).
  A simulation validation batch is running on this host: do NOT build `px4_sitl_default` and do NOT touch
  `build/px4_sitl_default`, `indi_project/bench/` or `indi_project/results/`. Keep the build at nice 19.
- Format: run astyle on the changed files only, the way `make format` does (check `Tools/astyle/` for the options
  file; run it inside the container with `indi_project/docker/run.sh`).
- Commit with conventional format, scope `indi`, one commit for library + module + tests, e.g.
  `feat(indi): complementary model/measured actuator state blend (MC_INDI_ACT_BLD)`; message body: why (integral
  action against a command/output gap, results/s2_tilt_diag.md), default 0 keeps v2. End the message with the lines
  `Assisted-by: Claude Sonnet` and `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Do NOT push.
