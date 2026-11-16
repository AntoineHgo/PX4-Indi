# metrics.py fixes for G1.3/G1.4 (session 29)

Scope: `indi_flight/bench/metrics.py`, `indi_flight/bench/tests/test_metrics.py` only. Nothing committed.

## What changed (bench/metrics.py)
- Constants `EFFORT_GRID_HZ = 400.0`, `EFFORT_LP_HZ = 50.0` (+ `EFFORT_MAX_GAP_S` 10 ms, `EFFORT_MAX_GAP_FRAC` 0.1 %, `EFFORT_PAD_S` 0.25 s) near the top.
- New helpers after `qcols`: `interp_quat`, `rate_track`, `att_track`, `estimator_error`, `butter2_lowpass_zero_phase` (hand-written 2nd-order Butterworth, bilinear design, steady-state init, odd-extension padding, forward-backward; scipy is NOT installed on the host, so no scipy path), `motor_rate_bandlimited`.
- `compute`, "rate / attitude tracking" block (was "rate tracking" + "attitude tracking"):
  - `rate_tracking`, `attitude_tracking` (primary) = truth: `sim_ground_truth` `angular_velocity[i]` (FRD, rad/s) and `q[]` (FRD->NED, same as vehicle_attitude), time axis = `timestamp_sample` via `ctrl_topic` (as before). Each has `source: "sim_ground_truth"`.
  - If `sim_ground_truth` is absent (or has no q/angular_velocity fields): primary keys are all `None`, `source: None`, warning added. No fallback.
  - `rate_tracking_estimate`, `attitude_tracking_estimate` = the old numbers (identical to the old values, verified on a real log).
  - `rate_estimator_error`, `attitude_estimator_error` = truth minus estimate, at the estimate sample times in the window (linear interp of truth rates, sign-aligned nlerp of truth quaternion): per-axis rms and mean, rotation angle rms.
- `effort`: `motor_rate_rms_per_s` = D-EFFORT-BW value (mean over motors; per motor in `motor_rate_rms_per_s_per_motor`), `motor_rate_rms_per_s_raw` = old pooled raw first difference, `motor_rate_bandwidth` = status/logged rate/gap fraction. Refusal (None + reason in `motor_rate_bandwidth.status` and in `warnings`): logged rate < 400 Hz (1 % tolerance), gap time (> 10 ms gaps plus uncovered window edges) > 0.1 % of the window, < 8 samples.
  Data from 0.25 s outside the window is used for the resample/filter so the edge transient stays outside the evaluation window. Stamps with non-increasing time (zero-dt publish-stamp pairs) are dropped before interpolation.
- Unchanged: step metrics (still estimate-based, `vehicle_attitude` / `vehicle_angular_velocity`), disturbance, motor_fault, position.

## Tests (bench/tests/test_metrics.py)
- New `test_truth_rate_attitude_tracking`: truth rates (0.3 const, 0.5 sin 2 Hz, 0) against setpoint -> analytic 0.2, 0.5/sqrt2, 0.05; truth attitude 0.1 rad roll offset -> 5.7296 deg; a very different estimate (+1 rad/s, +0.4 rad roll) changes neither; the diagnostics equal the offsets exactly; removing the estimate topics gives identical truth values; a 20 ms truth lag gives A*sqrt(1-cos(w*lag)) to 0.1 %; no `sim_ground_truth` -> None keys + warning, estimate keys intact.
- New `test_effort_bandwidth`: 5 Hz sine A=0.1 -> 2.2207/2.2207/2.2206 vs analytic 2.2214 (within 2 %) at log rates 400/800/1000 Hz; noise >= 100 Hz (std 0.01) changes it by 0.02 %/3.6 %/2.6 % (< 5 %); 150 Hz sine attenuated 1473x/1473x/113x (> 15x); refusals at 200 Hz and with a 20 ms hole (0.5 % of window), a 3 ms hole accepted; end-to-end through `compute`.
- Existing tests: rate/attitude tracking tests now read the `*_estimate` keys; `test_sample_stamp_over_publish_stamp` reads `motor_rate_rms_per_s_raw` for the stamp-choice comparison (the new value is robust to the stamp: 3.55 in both cases, analytic 3.554) and also asserts the new key.
- Breaks tried (each made at least one test fail, file restored afterwards):
  1. truth rate computed from `vehicle_angular_velocity` -> FAIL (1.2 vs 0.2)
  2. truth attitude computed from `vehicle_attitude` -> FAIL (28.6 deg vs 5.73)
  3. silent fallback to the estimate when `sim_ground_truth` is absent (rate) -> FAIL
  4. estimator-error sign flipped -> FAIL
  5. low-pass cutoff 50 -> 190 Hz -> FAIL (noise / 150 Hz / rate independence)
  6. rate < 400 Hz refusal removed -> FAIL
  7. gap refusal removed -> FAIL
  Not break-checked: `interp_quat` sign alignment, the 0.25 s padding, `EFFORT_MAX_GAP_S` threshold value.
- Suite: `python3 bench/tests/test_metrics.py` ALL PASS, `test_applied_timing.py` pass, `bash bench/gate_g1.sh g1.4` -> "existing tests PASS" (host has no pytest, so it runs each file). The filter was not cross-checked against scipy (not installed); it was checked against the analytic net response 1/(1+(f/fc)^4) via the 5 Hz gain and the 150 Hz attenuation.

## Real logs (old vs new)
Run: `python3 bench/metrics.py <log> --run-json <run.json> --out <scratchpad>`; logs are 800 Hz, window 30 s (hover) / 14 s (step).

`results/g16_sched_set_s26/speed4/hover/r1/flight.ulg` (old = archived metrics.json, matches the new `*_estimate` to 1e-15):

| metric | old (estimate) | new primary (truth) | estimator error (truth-est) rms |
|---|---|---|---|
| rate rms roll/pitch/yaw rad/s | 1.112e-3 / 0.860e-3 / 0.343e-3 | 0.942e-3 / 0.706e-3 / 0.177e-3 | 0.344e-3 / 0.331e-3 / 0.308e-3 |
| attitude rotation angle deg | 0.0456 | 0.556 | 0.654 |
| attitude roll/pitch/yaw deg | 0.0388 / 0.0379 / 0.0135 | 0.0454 / 0.0415 / 0.652 | 0.016 / 0.010 / 0.654 (yaw mean -0.652) |
| effort `motor_rate_rms_per_s` | 0.007162 (raw) | 0.003484 (band-limited); `_raw` 0.007162 | n/a |

`.../speed4/step_roll/r3/flight.ulg`: rate roll 0.1519 -> 0.1338 (truth), rotation angle 2.601 -> 2.628 deg (truth), yaw 0.046 -> 0.425 deg, effort 0.3388 -> 0.1045 /s (raw 0.3388 kept). Estimator error: roll rate rms 0.0216 rad/s, yaw mean -0.367 deg.

## Open doubts
1. Yaw: truth-minus-estimate yaw has a constant offset (-0.65 deg hover, -0.37 deg step) that dominates the truth `yaw_rms_deg` and `rotation_angle_rms_deg` in hover (0.0456 -> 0.556 deg). Not investigated: it is either a real EKF heading error or a heading-reference mismatch between the EKF frame (where `q_d` / hold yaw lives) and the simulator frame. If the latter, the truth attitude key is wrong by a frame constant and needs a yaw-offset-aware variant; the orchestrator should decide before it becomes a gate threshold.
2. Linear resampling to 400 Hz has no anti-alias filter (decision as specified): content above 200 Hz in logs > 400 Hz folds into the band. White-noise test shows up to 3.6 % at 800 Hz (limit 5 %); noise-heavy real logs could exceed that. The 800 Hz hover log changes 0.00716 -> 0.00348 (the old value was ~2x noise-dominated).
3. Step metrics (`step_metrics` driver) still use the estimate; defect 1 was only asked for tracking RMS. Consumers of `effort.motor_rate_rms_per_s` in old results (a11, errata) now see a different number; the old one is `_raw`.
4. Truth timestamps: `sim_ground_truth.timestamp_sample` is used as is (as in the position code); no check here that it shares the sim-time base with `actuator_motors`/`vehicle_angular_velocity` `timestamp_sample` beyond what earlier sessions verified (a15_truth_equal.py).
5. Per-motor mean replaces the old pooled rms; equal only if all motors have the same rms (they differ by < 0.6 % here).
