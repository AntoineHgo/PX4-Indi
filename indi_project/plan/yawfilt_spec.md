# Implementation brief: INDI yaw low-pass (D-yawfilt), for a delegated agent

Why: `results/sync_check_v0.md` sec. 3 and `DECISIONS.md` D-yawfilt. The yaw
filtered angular acceleration a_f,yaw is noisy and reaches the yaw torque
with gain 1/G1_Y; G1_Y identified = 7.4 (small), so yaw torque chatters.

## Change (firmware, one commit) — `src/lib/indi_rate_control/`

- New setter `setYawCutoff(float cutoff_hz)` (0 or non-finite = disabled).
- When enabled, an extra `math::LowPassFilter2p<float>` stage designed at the
  controller sample rate is applied to the yaw component of **both** a_f
  (after the existing derivative chain) and t_f (after the existing H
  filter), so a_f,yaw and t_f,yaw stay synchronised. Two filter instances,
  same coefficients. Redesign when the sample rate is redesigned
  (`designFilters`), reset in `resetStates()`; on enabling or changing the
  cutoff, reset the two new filters to the current unfiltered values (no
  transient). Roll and pitch are untouched. Cutoff above 0.45 x sample rate:
  treat as disabled (LowPassFilter2p behaviour, check it).
- The increment law is unchanged: dtau_yaw = (nu_yaw - a_f,yaw) / G1_Y
  (+ G2 term as it is), using the filtered pair.
- `indi_rate_status.angular_accel_filtered[2]` / `torque_filtered[2]` must
  report the post-yaw-filter values (that is what the controller uses).
- Static memory only, no new allocation; NaN handling as the existing code.

## Parameter (separate commit, mc_rate_control)

`MC_INDI_YAW_CUT`, float, Hz, default 0 (disabled, so behaviour is
unchanged until tuning sets it), min 0, max 100, decimal 1, in
`src/modules/mc_rate_control/mc_rate_control_params.yaml` next to the other
`MC_INDI_*`; wire it in `MulticopterRateControl::parameters_updated()` like
the other INDI params. Follow `.github/instructions/*` matching those paths.

## Tests

In `indi_rate_control_test.cpp` (gtest, same style as existing tests):
1. cutoff 0 gives bit-identical outputs to before for a fixed input sequence;
2. with cutoff 10 Hz at 250 Hz, white noise on yaw rate (fixed seed, simple
   LCG, no <random> allocation concerns) gives a smaller yaw increment std
   than with cutoff 0, roll/pitch outputs identical;
3. with a steady state where t_f,yaw * G1_Y = a_f,yaw, enabling the filter
   produces no output transient (reset to current values);
4. NaN cutoff disables the filter without fault.

Run `make tests TESTFILTER=indi_rate_control` and the SITL build through
`indi_project/docker/run.sh`; `make format` on changed C++.

## Validation (orchestrator)

Fly hover + step_yaw with `bench/params/indi_v1.params` plus
MC_INDI_YAW_CUT 0 and 10; compare hover motor-rate RMS with PID (0.037) and
the v0 value (0.300), and yaw step tracking.
