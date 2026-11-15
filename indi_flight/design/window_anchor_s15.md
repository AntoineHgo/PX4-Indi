# Window start anchored on the ULog nav_state transition (session 15)

Serves G1.6 (same-seed reproducibility). Problem: run.json `t_window_start_us` = offboard instant seen through the 1 Hz
MAVLink HEARTBEAT + 3.0 s, which jitters by up to ~1 s between same-seed runs (the ULog transition is 3.03-3.98 s before
that start).

## Diff summary
- `bench/metrics.py`: new `offboard_anchor_us(ulog)` = first vehicle_status sample with nav_state in (14, 23) and
  arming_state == 2 (if the log has no arming_state field, every sample counts as armed). `compute()` sets
  `w0 = anchor + OFFBOARD_SETTLE_S (3.0 s)`. Fallback to the old rule (max of run.json start and span start) when the log
  has no armed offboard sample; then `start_source = "runjson"` and a warning is added.
- Window END and DURATION: unchanged semantics. End = absolute run.json `t_window_end_us`, still clipped to the end of the
  offboard span. There is no fixed duration: duration = end - start, so it now varies with the start (30.0-31.0 s hover,
  14.1-14.9 s step_roll, 23.4-24.2 s traj), by the old start jitter plus the run.json end jitter. The end is an
  absolute sim.t value set when the scenario segments finish; its own jitter is NOT removed by this change.
- `out["window"]` gains: `start_source` ("ulog_nav_state+3.0"), `runjson_start_s` (old start), `ulog_anchor_s`.
- `bench/tests/test_metrics.py`: new `test_window_anchor_from_ulog`; existing end-to-end case's synthetic vehicle_status
  moved 3 s earlier (anchor + 3 s = old t[0]) so its semantics are unchanged.

## Other users of the window (checked)
- trajectory `t0_us` guard (`w0 <= t0_us <= w1`): t0_us is set by the runner after the 3 s hold segment (e.g. t0 58.248 s vs
  run.json start 55.248 s), and the new start is 0.03-0.98 s EARLIER than run.json start, so the guard still passes
  (all 30 runs: time_base ok, verify below). Extra window samples (<=1 s) precede t0: analytic reference is the hold
  position there (traj_phase(t<=0)=0), so they are pure hold-error samples and add a small, deterministic dilution.
- step events (`ev["t_us"]`): absolute run.json times, independent of the window; step metrics unchanged (rise/settle
  means are bit-identical, see table).
- motor_fault event / disturbance onset: absolute `event_us` / `onset_us`, evaluated from the event to `w1`; start
  moved earlier cannot cut them. Not exercised by G1.6 scenarios (unverified on a fault/disturbance run).
- rate/attitude RMS, position max_dev, trajectory error: use `inwin` and change by the ~0.2-1.0 s of added hold data.
- traj `max_dev_3d` unchanged (peak is mid-trajectory); hover `position.max_dev_3d_m` unchanged (peak mid-window).

## Tests
- `python3 indi_flight/bench/tests/test_metrics.py`: ALL PASS with the fix (new case: transition at 5.3 s, run.json start
  9.0 s i.e. 0.7 s late, an unarmed nav_state-14 sample at t=0 ignored; asserts start 8.3 s, runjson_start 9.0 s,
  source "ulog_nav_state+3.0", end 15.0 s; plus fallback case -> "runjson").
- Broken once (`elif False and anchor is not None`, i.e. use run.json start): the new case FAILS with
  `AssertionError ... start_s 9.0 ... start_source 'runjson'`. Fix restored, all pass again.

## Re-score (no flights)
30 runs (`results/det_g16/*/r1-5`, `results/det_g16_s4/*/r1-5`) rescored in place with the runner's command line
(`metrics.py flight.ulg --run-json run.json --out metrics.json`). Old files kept as `metrics_pre_s15.json` in each run dir
and `spread_pre_s15.json` per root. Spread outputs: `results/det_g16/spread_s15.txt`, `results/det_g16_s4/spread_s15.txt`
(the txt files only hold the per-scenario leaf counts; the numbers are in `spread.json`, overwritten, with the old one in
`spread_pre_s15.json`).

### window.start_s spread, max-min over r1-r5 (s)
| root / scenario | old (run.json) | new (ULog anchor) | new - old range |
|---|---|---|---|
| s1 hover | 0.344 | 0.008 | -0.54..-0.20 |
| s1 step_roll | 0.548 | 0.008 | -0.90..-0.36 |
| s1 traj_lemniscate | 0.468 | 0.004 | -0.69..-0.22 |
| s4 hover | 0.952 | 0.016 | -0.98..-0.03 |
| s4 step_roll | 0.356 | 0.012 | -0.49..-0.12 |
| s4 traj_lemniscate | 0.756 | 0.012 | -0.96..-0.20 |

Residual 4-16 ms = real transition-instant jitter in ULog time (vehicle_status sample timing), not a measurement artifact.

### Same-seed metric spreads, mean / spread (rel), before -> after
| metric | s1 old | s1 new | s4 old | s4 new |
|---|---|---|---|---|
| traj truth rms_3d (m) | 0.704 / 0.0195 (2.8%) | 0.697 / 0.0199 (2.9%) | 0.703 / 0.0224 (3.2%) | 0.696 / 0.0292 (4.2%) |
| traj truth max_dev_3d (m) | 1.378 / 0.0479 | same | 1.381 / 0.0424 | same |
| step rise mean (s) | 0.179 / 0.0113 (6.3%) | same | 0.176 / 0.0136 (7.7%) | same |
| step settle mean (s) | 0.313 / 0.021 (6.7%) | same | 0.308 / 0.022 (7.1%) | same |
| step roll rate rms (rad/s) | 0.164 / 0.0113 (6.9%) | 0.161 / 0.0104 (6.4%) | 0.163 / 0.0165 (10.1%) | 0.162 / 0.0181 (11.2%) |
| hover attitude rms, roll (deg) | 0.0363 / 0.0054 (14.9%) | 0.0362 / 0.0052 (14.5%) | 0.0350 / 0.0083 (23.7%) | 0.0349 / 0.0083 (23.7%) |
| hover max_dev_3d (m) | 0.0409 / 0.0040 | same | 0.0434 / 0.0304 | same |

## Finding
The window start was NOT the dominant source of the same-seed spread. The start jitter fell from 0.34-0.95 s to
0.004-0.016 s, yet the metric spreads are essentially unchanged (changes within +-1 pt relative, some slightly worse:
s4 traj rms_3d 3.2% -> 4.2%, s4 roll-rate rms 10.1% -> 11.2%). Step metrics are independent of the window (event-time
based). The remaining spread comes from the flights themselves (and from the window END, still the absolute run.json
sim.t,) -- G1.6 spread is not explained by window anchoring.

## Unverified
- "hover attitude rms" in g16_s13.md (0.042 / 0.035) is not any single leaf I could match; I report roll_rms_deg
  (pitch: s1 0.0328/0.0090 -> 0.0328/0.0095, s4 0.0316/0.0054 -> 0.0314/0.0054).
- Window END jitter not addressed (still run.json absolute); an end anchored the same way (start + fixed scenario
  duration) was not tried, would be the next step if the spread is to be attributed to window edges.
- motor_fault / disturbance scenarios not re-scored (no such runs in G1.6); only reasoned about above.
- Trajectory time_base status checked after rescore: 10/10 traj runs "ok" (both roots); no rescore errors.

## Orchestrator follow-up (S15): window end anchored too
- metrics.py: end = anchored start + run.json duration (`t_window_end_us - t_window_start_us`); the test case asserts
  end 14.3 s / duration 6.0 s (fails with the absolute end, passes with the fix; `ALL PASS`).
- Re-scored the 30 runs again (in place). Window start spread 0.004-0.016 s, duration 14.000-14.016 / 23.220 /
  30.000-30.012 s (the run.json duration itself varies by <= 16 ms).
- Spreads after both fixes vs `spread_pre_s15.json`: no non-window metric changed by more than 30 % of its spread
  (only `allocator.n_samples` 1 -> 0). Verdict: window jitter did not drive the same-seed spread; the spread is the
  flights' own non-determinism (gz not lockstepped, gyro differs from +28 ms after arm, S13). This is the G1.6(c)
  cause; the bound is the measured spread table (`g16_s13.md`, unchanged to 30 %).
- Second key on the window bounds: T29 (haiku), `results/second_key_window_s15.md`.
