# Implementation brief: yaw rate filter in nu (D-yawnu), for a delegated agent

Why: `results/tuning/r2f_yc2.md`, `DECISIONS.md` D-yawnu. Builds on
D-yawfilt (`plan/yawfilt_spec.md`, already implemented).

## Change (firmware, one commit) — `src/lib/indi_rate_control/`

- In `IndiRateControl::update()` (`indi_rate_control.cpp`, nu computed at
  ~line 210 as `_gain_k.emult(rate_sp - rate)`): when the yaw cut-off is
  enabled, use `rate_yaw_f = _yaw_rate_lpf.apply(rate(2))` instead of
  `rate(2)` in nu_yaw. Roll/pitch and the setpoint unchanged.
- `_yaw_rate_lpf`: a third `math::LowPassFilter2p<float>` with the same
  design as the two existing yaw filters (same sample rate, same cut-off;
  designed, reset and re-initialised exactly where they are; on enabling or
  changing the cut-off reset it to the current rate(2), no transient).
- Cut-off 0 / disabled: bit-identical to current behaviour (filter not
  applied). Invalid inputs: same handling as the existing code; the filter
  must not be fed NaN (apply after the input validity check).
- `indi_rate_status.nu[2]` reports the nu actually used.
- Update the YAW_CUT param description in
  `src/modules/mc_rate_control/mc_rate_control_params.yaml` (same commit or
  a separate docs-only one) to say it also filters the yaw rate feedback.

## Tests (`indi_rate_control_test.cpp`, existing style)

1. cut-off 0: outputs identical to before for a fixed input sequence (the
   existing bit-identity test may already cover it; extend if not);
2. cut-off 2 Hz at 250 Hz, white noise on yaw rate only (fixed-seed LCG):
   yaw increment per-sample-change RMS smaller than with D-yawfilt alone
   would give — simplest: compare against cut-off 0 and check a reduction
   factor > 3; roll/pitch outputs identical to cut-off 0;
3. constant yaw rate error, steady state: nu_yaw converges to K_Y*(r_sp-r).

Build: SITL in Docker (`indi_project/docker/run.sh`, see
`bench/RUNNER_NOTES.md`), run the lib gtest, `make format` on changed files.
