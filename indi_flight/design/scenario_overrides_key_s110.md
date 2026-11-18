# Second-key review, commit fc3ef9e626 (scenario overrides, parametrised wind, g3_run hooks)

Read-only review, coded to the G3 spec (g3_sample.py draw structure, GATES.md G3 FINAL). The author's design notes were not read before writing. No simulation run. Tests run as scripts (no pytest installed). The mutation tests were done on a copy under the scratchpad.

(Process note: my first mutation attempt had a failed `cd` and briefly modified `disturbance.py` and `g3_run.py` in the repo. Both were restored with `git checkout --` and `git status` shows them clean; the committed content is unchanged.)

## Findings

### BLOCKING
None in the code as committed, if the items below are accepted and logged as gate-visible deviations. B-1 is a project-rule violation that was already there before this commit. It is rated MAJOR (M-1) because the commit did not introduce it. The orchestrator may re-rate it BLOCKING for G3 wind items.

### MAJOR
- **M-1 Wind drag is not air-relative** (`disturbance.py:127-131`, `gust_x`: `d = af.c_drag * v * abs(v)`, v = wind speed alone). The old code had the same form (`f = (af.c_drag * v * abs(v), 0, 0)`), so this is pre-existing and not introduced by the commit. The injector only gets `(t, af)` and has no vehicle velocity, so it cannot be air-relative. The project requires air-relative drag for injectors. As it stands the wind is a pure force, with no damping from vehicle speed, and a vehicle drifting downwind sees too much force. Fix: pass the vehicle velocity into `gust_x`, or log this as a declared deviation.
- **M-2 eRPM loss window is changed from the draw** (`g3_run.py:143-149`). Drawn: one motor, start in [1,5] s after hold start, duration `LOSS_S` = 2 s (`g3_sample.py:176-178`, `LOSS_S` at line 43). Applied: loss from the start of `traj` or `stick` to the start of `hold`, about 17.8 to 18 s, roughly 9 times longer, beginning at the segment start. The loss is therefore much harsher than the spec. It is recorded in `notes["tel_loss"]`, so it is not silent, but every G3 eRPM-loss run flies a different test than the sampler specifies. Add a time-based hook (start offset and duration), or move the gate text.
- **M-3 Weak motor and saturation share one `motor_fault` slot.** `g3_run.py:182-188`: when saturation is on, weak motor is dropped and put in `not_applied`. The sampler allows both only in the C3 corner (sat pin) if `weak_on` also happens in that run. The drop is loud, but that run is not the drawn plant. Also `scenario_overrides.py:70` only allows one `motor_fault` dict. Fix: let `motor_fault` be a list, or fold the weak motor into per-motor scales (a `motors` dict with a scale per motor).

### MINOR
- m-1 Thrust sag. The ramp runs over the whole scenario window, from `sim.t` at start (settle included) to the end of `hold`, as a 0.5 s staircase with v rounded to 4 decimals (`run_scenario.py:910-920`). Drawn `ramp_s` = 10 s (`g3_sample.py:37`). The sag reaches `scale` only at the end of the window. Logged in `notes`.
- m-2 Motor-fault timing. The weak-motor and saturation steps happen at the start of `traj`/`stick`, which is 3 s after hover start. The sampler hook says `t0: hover start` (`g3_sample.py:250-254`). The EC min/max are scaled by sqrt(thrust_scale) and rounded to int (`run_scenario.py:~898-903`; pre-existing). The rounding error is below 0.1 % for the sampler's ranges.
- m-3 Wind timing. Wind starts at the start of the main segment (`dist_segment` = `traj`/`stick`), with a 2 s ramp, a 10 s hold, a 1 s gust, then a hold; the profile is 28 s against a window of about 21 s. The gust therefore falls at 12 to 13 s into the main segment and is inside the window. Drawn `gust_offset_s` = 0.0 (hold start) is not used (`notes["wind"]`).
- m-4 Frame. `dir_deg` is documented as from world +x towards +y, where the air moves to. The gz world is ENU (x east, y north), which is counter-clockwise from east. The sampler draws `dir_deg` uniformly in [0, 360), so mirroring it into NED would not change the distribution. No unit or sign error exists, but the frame is not stated against PX4 NED in the sampler. Default profile: `dir_deg == 0.0` takes the old `(d, 0, 0)` branch and `wind_speed` defaults equal the old constants, so it is bit-identical (checked by `test_gust_defaults_bit_identical`, and it passes).
- m-5 `--sched` guard. `run_scenario.py:693` now tests `sc_base`, not the merged scenario, so `--sched` with overrides passes the check that says hooks "need the runner's segment times". With `--sched` the runner steps `sim.run(dur)` per segment, so the hook times probably work, but with `--sched-anchor` the player timeline starts at `sched_t0` while hooks and disturbance onset use `sim.t`. Not verifiable without a simulator. Needs a sim check before the pre-test.
- m-6 Merge and validation. Merge is shallow (`out.update`) and a scenario that already has a hook key gets it replaced whole. That is safe for the stock O1 and stick scenarios, which carry none of these keys (checked: `o1_lemniscate` and `stick_zsine_o6` have none). A scenario with a `motor_fault` plus an override gets only the override's fields. Segment validation checks names against the merged scenario's segments. The segments the G3 runs use (`settle`, `traj`/`stick`, `hold`) all exist. The validation does not check that `erpm_loss.end` differs from the last segment, nor that `dist_segment` leaves enough time for the 28 s profile.

## Per-factor audit (unit, sign, frame, timing)
| factor | reaches hook? | value altered? |
|---|---|---|
| thrust_sag scale | yes, in (0,1], `thrust_sag.scale` | ramp length and timing differ (m-1) |
| saturation scale | yes, `motor_fault.motors=[0..3]`, `thrust_scale` | step at main segment (m-2) |
| weak_motor | yes unless saturation | dropped when saturation is on (M-3) |
| tel_loss | yes, motor index same | window altered (M-2) |
| wind steady, peak (total), dir | yes, floats exact (`repr(float())`), `amp = peak - steady` | gust offset unused (m-3) |
| delays, GNSS, vibration | unchanged, via CLI flags, `int()` of integer-valued ms (not changed by this commit) | no |

## Test efficacy (mutations in a temp copy)
Caught by tests:
- wind direction `sin` replaced by `cos` in `gust_x`: `test_gust_parametrised` FAILS.
- `g3_run.py` writes `gust_amp_ms` as the wind `peak`: `test_g3_run` FAILS (one or two tests).
- `g3_run.py` writes dir_deg as 0.0: `test_overrides_applied_and_valid` FAILS.
- sag scale forced to 1.0 or saturation thrust_scale forced to 1.0: `test_overrides_applied_and_valid` FAILS.
- `wind_flags` doubles the value: `test_validation` FAILS.

NOT caught (tests pass with the line broken):
- `disturbance.py:233` (the CLI `main()`): `am=pk - st` changed to `am=pk` (the peak/amp conversion). The CLI path has no test, so a wind-peak error of `steady` m/s would go through. MAJOR for wind validity (gust would be steady m/s too strong). Add a test of the argument-to-profile function, e.g. split the lambda into a pure function.
- `g3_run.py`: erpm_loss motor index shifted by one (`(motor+1) % 4`): no test fails. Motor-index and sign mapping for erpm_loss is not checked.
- `g3_run.py`: weak-motor `segment` changed from `main_seg` to `"hold"`: no test fails (segment timing of the weak motor is not asserted).

## Verdict
The interface does what it says for wind, sag and saturation. Three behaviours are unchecked by tests (CLI wind peak, erpm_loss motor, weak-motor segment) and three drawn factors are altered (M-1 to M-3). Recommend fixing the test gaps and deciding on M-2 and M-3 before the G3 pre-test.
