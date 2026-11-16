# A-23 yaw test: MC_INDI_G1_Y 215 on the S44 indi_g1derived setup (S45)

Question: does MC_INDI_G1_Y being 7x too low cause the motor-command chatter seen in S44 (anomaly A-23)?
Single SITL flight, one parameter changed against S44 `indi_g1derived` (`MC_INDI_G1_Y 215` added; no other change).
No firmware, bench script, indi_project file or S44 result was changed.

## Setup
- Scenario `hover_long`, controller `indi_m3a`, seed 1, speed 4, model quad5in, `--sim v2`, runner `indi_flight/bench/run_scenario.py`.
- Params: `a23_indi_g1y.params` = copy of `stage2_s44/a23_test/a23_indi_g1derived.params` plus the appended lines
  `# S45 ...` (comment) and `MC_INDI_G1_Y 215`. The S44 file has no MC_INDI_G1_Y line, so the G1_Y value is the only difference.
- No command-record argument was passed to the runner (UNVERIFIED that the runner has no such option; the argparse list was
  only partly read). The S44 README's `run.json` reference is an output record of stage2_s40, not an input.
- `docker ps` was empty before the flight and after it. Container names: `px4-indi-s45a23y` (flight), `px4-indi-s45chk` (checkers).

## Commands (repo root, Docker via `indi_project/docker/run.sh`)
Flight (`-t 900`):
```
indi_project/docker/run.sh -n s45a23y -t 900 'python3 indi_flight/bench/run_scenario.py --scenario hover_long --controller indi_m3a --seed 1 --speed 4 --model quad5in --sim v2 --params indi_flight/results/stage2_s45/a23_yaw/a23_indi_g1y.params --out indi_flight/results/stage2_s45/a23_yaw/indi_g1y' > indi_flight/results/stage2_s45/a23_yaw/indi_g1y_stdout.log 2>&1
```
Checkers (`-t 900`, run in the container as in S44):
```
indi_project/docker/run.sh -n s45chk -t 900 "python3 indi_flight/bench/limit_cycle_check_s44.py LOG indi_g1y/limit_cycle.md indi_g1y && python3 indi_flight/bench/motor_chatter_s44.py LOG indi_g1y/motor_chatter.md"
```
where LOG = `indi_flight/results/stage2_s45/a23_yaw/indi_g1y/flight.ulg`. Checker stdout: `indi_check_stdout.log`.
The label argument `indi_g1y` was passed to the limit-cycle checker. `motor_chatter_s44.py` takes only LOG and OUT.

## Exit status
- Flight: shell exit 0. `run.json`: exit_status `ok`, error `null`, wall_time 49.4 s, climb done 39.67 s,
  hover_thrust_estimate 0.13668, metrics_status `ok`. The flight did not need a retry.
- Checkers: exit 0 for both scripts.
- Parameter check (pyulog, host python, `ULog(...).initial_parameters`): `MC_INDI_G1_Y 215.0`,
  `MC_INDI_G1_R 1756.0`, `MC_INDI_G1_P 1599.49`, `MC_INDI_INJ_AMP 0.0`. Confirms the parameter took effect.
  `MC_RATE_CTL_TYPE` was not returned by `initial_parameters` (value None). UNVERIFIED that it is 1 in this log;
  `run.json` `boot_params` shows `MC_INDI_EN 1`, which is the setting the runner applies when `MC_RATE_CTL_TYPE` is 1.

## Git state (differs from S44)
- `run.json` records commit `7825fca2326886403b2205d06c79f563a0cc0e55`, `dirty: true`.
  S44 `indi_g1derived` recorded commit `80bcd82dea`, not dirty. The flight was made on a dirty working tree; not investigated.

## Results side by side with S44 indi_g1derived
Window 52-82 s since boot, 800 Hz logged. S44 numbers from `stage2_s44/a23_test/README.md` and `motor_chatter.md`.
S45 numbers from `indi_g1y/limit_cycle.md`, `indi_g1y/motor_chatter.md` and `indi_check_stdout.log`.

| Metric | S44 indi_g1derived (G1_Y not set) | S45 indi_g1y (MC_INDI_G1_Y 215) |
|---|---|---|
| Motors < 0.005 fraction (control[0..3]) | 0.460, 0.464, 0.464, 0.464 | 0, 0, 0, 0 |
| Motor mean (control[0..3]) | 0.2493 | 0.1367 (all four) |
| Body-rate RMS x / y / z (rad/s, mean removed) | 0.04528 / 0.03683 / 0.4231 | 0.0068 / 0.0056 / 0.0017 |
| torque_setpoint_achieved fraction (samples) | 0.0733 (5988) | 1.0 (5989) |
| Mean abs unallocated torque x / y / z | 1.6e-8 / 1.7e-8 / 0.612 | 4.22e-9 / 4.28e-9 / 4.16e-9 |
| Pitch dominant frequency | 8.008 Hz | 2.148 Hz |
| Motor-command dominant frequency (actuator_motors control[0], f >= 0.5 Hz) | 45.898 Hz | 45.703 Hz |
| Yaw torque_sp[2] std (indi_rate_status) | 0.8954 | 0.0008216 |
| Logged MC_INDI_G1_Y | not set | 215.0 |
| Extra: pitch PSD peak / median (checker A-23 ratio) | 4.251e6 | 7.208e6 |
| Extra: pitch sinusoid amplitude (checker) | 0.0233 rad/s | 0.00364 rad/s |
| Extra: pitch RMS, largest 1 s bin in armed period | 0.798 rad/s at 35.0 s | 0.0202 rad/s at 51.0 s |

## Notes and UNVERIFIED items
- UNVERIFIED: `motor_chatter_s44.py` writes the heading "S44 motor-command chatter: a23_test / indi_g1derived" into this
  report regardless of input. The `Log:` line shows the correct path (`stage2_s45/a23_yaw/indi_g1y/flight.ulg`); the heading is a hard-coded label.
- UNVERIFIED: `esc_rpm` unit (mechanical or electrical) and the 2700 rad/s scale used for u_meas (script's own note).
  The S45 motor_chatter.md states the same, so the esc-based comparison is not used in the table above.
- UNVERIFIED: the 17 Hz component named in A-23 was not looked for; the checker does not report it.
- UNVERIFIED: the PSD peak/median ratio is ill-conditioned for a near-noise-free spectrum (see S44 README); not used as a pass/fail here.
- The 46 % of motor samples at zero in S44 and the 8 Hz pitch oscillation are not present in S45 window data (0 % at zero motors).
- Single seed (1), single flight. Only the one parameter listed above differs from S44 `indi_g1derived`, except for the git commit state (see above).
- No interpretation beyond the numbers is given here.
