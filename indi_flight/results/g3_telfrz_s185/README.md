# G3 frozen-telemetry injector (S185)

## Diff
- `src/modules/simulation/gz_bridge/GZMixingInterfaceESC.{cpp,hpp}`, `module.yaml`: new `SIM_GZ_ERPM_FRZ` (int32 bitmask, 0..255, default 0, read at runtime in updateParams like LOSS). Bit i set: in the ESC_FB 2 branch motor i skips the decode update, so `_erpm_last_rpm[i]` (value at the moment the bit was set) is published bit-identical with a fresh timestamp and no `_erpm_errors` increment. Latency delay line keeps running. Frozen takes precedence over loss/drop on the same motor. +21/-1 lines. No other firmware touched.
- `indi_flight/bench/scenario_overrides.py`: `erpm_frozen {motor,start,start_offset_s,duration_s}` (timed only, same window validation as timed erpm_loss).
- `indi_flight/bench/run_scenario.py`: new pure `timed_windows()`; the timed-loss branch is generalised so loss and frozen windows in the same segment may overlap; logs `meta["erpm_frozen"]` with `on_us`/`off_us`; clears param at end.
- `indi_flight/bench/g3_run.py`: tel_frozen -> `ov["erpm_frozen"]` + `applied["tel_frozen"]` (+ note); no factor is left in not_applied except none. `g3_sample.py`: hook label only.
- Tests: `test_g3_run.py` (hook-missing abort test replaced by `test_no_factor_left_unapplied` and `test_erpm_frozen_drawn_motor_and_window`), `test_run_scenario_hooks.py` (`test_timed_windows_overlap_and_sum`). The four bench self-tests (g3_run, run_scenario_hooks, scenario_overrides, g3_sample) pass on the host.

## Detector (firmware, read only)
`IndiMeasuredTorque::evaluateWindow`: motor flagged frozen when rpm is bit-identical (memcmp) for MC_INDI_ERPM_FRZ (0.5 s) while armed AND the motor command varied (max-min) > 0.02 in that window; a constant command restarts the window (constant rpm is legitimate). An error-count change counts as a dropped frame, so the injector must not increment it (it does not). Status: `motor_frozen_mask` in the torque model result; ulog `indi_rate_status.measured_torque_in_use` goes 0 on fallback.

## Probe
`indi_project/docker/run.sh -n s185fly -t 600 -- python3 indi_flight/bench/run_scenario.py --controller indi --params indi_flight/results/g5_freeze_s157/params.params --model quad5in --speed 4 --sim v2 --scenario hover --scenario-overrides indi_flight/results/g3_telfrz_s185/ov.json --seed 185 --out indi_flight/results/g3_telfrz_s185/probe`
(build: `make px4_sitl_default` in the same container, rc 0, build.log). ov.json: motor 0, segment hold, +12 s, 3 s. status ok. Raw probe/ logs untracked.

## Log checks (probe/flight.ulg)
- run.json: on_us 67173000, off_us 70173000 (3.000 s). esc_status instance 0 (the one INDI subscribes to): 2337 frames in [on,off), esc[0].esc_rpm unique = {9542}, bit-identical; max timestamp gap 3.75 ms (fresh stamps). Frame at the log's first frozen sample equals the value before (9542). Other motors in the window: 2 distinct values each (live, quantised).
- esc[0].esc_errorcount 0 throughout (min=max=0 inside and +-4 s around).
- Outside the window motor 0 is live but coarse: 3 distinct values in the 4 s before (9500..9542), 2 in the 4 s after (9528..9542). Eight-bit-ish quantisation of the eRPM model plus a steady hover means the frozen value is close to the live one; the freeze is proven by the bit-identity and the timing, not by a rpm jump.
- INDI detector: did NOT trip. measured_torque_in_use stayed 1, fault 0, rate_sp_stale 0 through the window. Reason: hover command of motor 0 varied only 0.0006 (max 0.5 s peak-to-peak) < 0.02, so by design every window restarts. Vehicle stayed fully in control (hover position rms 3d 0.020 m, roll/pitch rms 0.16/0.14 deg).

## Unverified / flags
- The detector TRIP path through the injector was not exercised: needs a manoeuvring scenario (e.g. v2_drop_att / G3 main segments with command variation). The G3 campaign will cover that; a one-run follow-up with v2_drop_att and the same ov.json (start segment "up") would confirm it.
- esc_status instance 1 exists in the log with live motor-0 rpm throughout (many distinct values in the window). Its publisher was not identified; INDI uses the default subscription (instance 0). Worth a look before concluding on other consumers.
- `make check_format` / astyle not run (tabs, style matched by hand).
