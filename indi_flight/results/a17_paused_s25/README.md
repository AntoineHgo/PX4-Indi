# A-17 paused-start test (session 25): result NEGATIVE, G1.6(a) not met

Hypothesis tested: Commander loop phase differs per run because PX4 starts while gz already advances sim time
(wall-clock race). Test: start gz paused, unpause after PX4 start-up.

## Code change (indi_flight/bench/run_scenario.py, uncommitted)
- `start_gz()` (~l.208-212): drops `-r` when `--paused-start` (`run_flag`). Default behaviour unchanged.
- `gz_clock()` / `unpause_gz()` (~l.223-240): `gz service -s /world/default/control --reqtype gz.msgs.WorldControl
  --reptype gz.msgs.Boolean --timeout 5000 --req 'pause: false'`; writes `<out>/unpause.txt` (wall time, reply, gz clock
  before and after the unpause).
- `start_px4()` (~l.262): if `--paused-start`, `wait_log(--unpause-after)` then `unpause_gz()` before waiting for
  "Startup script returned successfully".
- argparse (~l.554): `--paused-start`, `--unpause-after` (default `Startup script returned successfully`).
- Script: indi_flight/bench/a17_paused_hover.sh (runs + second_key_player + a17_commander_phase per run).
  r1..r5 were flown as `r1` then `r2 r3 r4 r5`. r1..r5 were flown BEFORE the `gz_clock` diagnostic was added to
  `unpause_gz`; only diag_r6 (extra run) has the clock evidence.

## Unpause point and why
Start-up CAN complete with sim time frozen: the rcS `sleep` / gz_bridge waits did not block (the gz clock topic is
published while paused, gz_bridge init got its clock; `Startup script returned successfully` appears and unpause happens
at wall ~15.0 s in all runs). So the latest possible point is used: after "Startup script returned successfully"
(commander, gz_bridge, sensors, logger, sim_scenario_player all started with sim time at 0).
Evidence in diag_r6/unpause.txt: `clock_before` sim = {} (0 s), `clock_after` (about 0.4 s wall later) sim = 0.32375 s.
The later runner steps (param set, logger restart, wait "Ready for takeoff") run after the unpause, as in the default
flow.

## Pre-test (hover_r1)
Armed, switched to offboard, hovered, landed, flight.ulg written; applied rows exact (arm 30.000000 s, mode_offboard
52.000000 s). Then r2-r5 flown.

## 5-run table (absolute sim time, us; mod = mod 10000 us)
| run | armed | arm mod | offboard | offboard mod |
|---|---|---|---|---|
| r1 | 30003750 | 3750 | 52013750 | 3750 |
| r2 | 30001250 | 1250 | 52011250 | 1250 |
| r3 | 30010000 | 0    | 52012500 | 2500 |
| r4 | 30007500 | 7500 | 52017500 | 7500 |
| r5 | 30006250 | 6250 | 52016250 | 6250 |

Commander phase (a17_commander_phase.py, vehicle_status/actuator_armed/vehicle_control_mode/failsafe_flags, whole log):
r1 3750 (100 % of messages in one bin). For r2..r5 the `armed mod` / `offboard mod` lines in status.txt are the
phases above; per-run phase.json holds the histograms. r3 shows arm and offboard at different phases (0 and 2500), so
the phase is not even constant within a run. (I did not open the r2..r5 histograms individually: unverified detail.)

Spread across runs: arm 8.75 ms (30001250..30010000), offboard 6.25 ms (52011250..52017500).
S24 without the fix: 5.0 / 6.25 ms. G1.6(a) threshold 2.5 ms: NOT met, no improvement.

## Verdict and reading
The wall-clock-race-at-start hypothesis is rejected: with gz frozen at t = 0 through all PX4 start-up, the phase is still
spread over the 10 ms loop (5 distinct values in 5 runs).
Likely real cause (from source reading only, NOT tested): Commander::run (src/modules/commander/Commander.cpp
l.2209-2211) does `px4_usleep(10000)` as a relative sleep after variable-duration work and skips the sleep when a
vehicle_command or action_request is pending. gz keeps stepping sim time while PX4 computes (lockstep blocks PX4 on the
clock, not the clock on PX4 CPU work), so each iteration's sim duration is 10 ms plus a jitter-dependent number of 1.25 ms
steps, and the phase random-walks. A fixed start time cannot fix that.
Next-session options: (a) compare phases at speed 1 vs 4 (does the walk scale with RTF), (b) look at the Commander
iteration timing from the existing log streams to check the random walk, (c) measure G1.6(a) on the scenario player's
applied timestamps, or accept the 10 ms Commander granularity.
