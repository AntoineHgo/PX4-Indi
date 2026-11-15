# Port 1a: SITL scenario runner into indi_flight/bench (gate G1 measurability)

Nothing was run: no sim, no Docker, no build. Only py_compile, test_metrics.py and a Sim/sends.csv smoke test.

## Files copied from indi_project/bench (cp, then edited)
run_scenario.py, scenarios.py (unchanged), model_variant.py (unchanged, imported at run_scenario.py:25),
disturbance.py (unchanged, spawned at run_scenario.py ~452 by path next to the script).
params/ NOT copied: the runner never reads params/ itself, `--params FILE` is a CLI argument. Copy the needed
files when a batch is defined.

## Changes to indi_flight/bench/run_scenario.py (line numbers of the new file)
- 4: docstring command now points to indi_flight/bench/run_scenario.py (docker launcher indi_project/docker/run.sh kept).
- 27-30: REPO is now `../../..` (PX4 repo root, so BUILD=build/px4_sitl_default still resolves); new RESULTS_DIR =
  indi_flight/results.
- 429, 444-445: `--out` is optional, default `indi_flight/results/<scenario>_<controller>_s<seed>`.
- 96-98 Sim.__init__: wall0, sends buffer, sends_pending. 101-122: SENDS_COLS, log_send(), write_sends().
- 189-193 set_param(name, value, kind, intended_us, extra): logs a row (blocking), stamps wall_after_s in finally.
- 206 cleanup(): write_sends() first, inside its own try (written even on a failed run).
- 265-268 pump(): on each ATTITUDE, fills sim_time_after_us of rows from blocking calls (first tick after return).
- 335/342/357/362: send_pos / send_pva / send_att / send_rate each log one row.
- 582 sag_tick: its set_param is logged with kind="sag" (one row per step, not also a "param" row).
Rows are kept in a list and written once; per-send cost is one list append and a short f-string.

## Changes to indi_flight/bench/metrics.py
- Docstring (7-8), OFFBOARD_NAV_STATES = (14, 23) at 60, offboard_span uses np.isin at 68, warning text at 299.
- tests/test_metrics.py: ALL PASS (it does not cover nav_state 23 specifically; unverified on a real ULog).

## sends.csv schema (<run_dir>/sends.csv, one header row)
kind: send_pos | send_pva | send_att | send_rate | param | sag
intended_sim_time_us: sim time of the latest ATTITUDE tick when the call was made (the tick that triggered it)
sim_time_before_us: same tick (equal to intended, except for future callers passing intended_us)
sim_time_after_us: blocking rows only: time_boot_ms of the first ATTITUDE after the call returned (upper bound);
  empty for sends and for blocking rows with no later tick
wall_time_s: seconds since Sim() creation at call start; wall_after_s: at return (blocking rows only)
payload: `;`-separated k=v. param: NAME=value. sag: NAME=v;frac=;sched_us= (nominal 0.5 s grid time).
setpoints: x,y,z[,vx,vy,vz,ax,ay,az],yaw | roll,pitch,yaw,thrust | p,q,r,thrust (5 significant digits).
Time resolution is 1 ms (ATTITUDE time_boot_ms), sim_time_after only has tick granularity (10 ms at 100 Hz).

## NOT fixed
- Setpoints still go Python -> MAVLink UDP on the ATTITUDE tick via pump(); arrival step still depends on host load.
- set_param is still the px4-param CLI: blocks wall time while sim time advances; sim_time_after - before measures it.
- The sag is still a 0.5 s staircase of param sets paced on wall/pump time, not a sim-time-exact ramp.
- sends.csv gives the *send* time, not the *applied* time: the applied time needs the ULog (below).

## Proposed bench/applied_timing.py (not written)
Inputs: run_dir (sends.csv, flight.ulg). For each row, find the first ULog event at or after intended_sim_time_us:
- send_pos / send_pva: first trajectory_setpoint sample whose position/velocity matches the payload
  (tolerance 1e-3) and timestamp >= intended; send_att / send_rate: first vehicle_attitude_setpoint /
  vehicle_rates_setpoint sample matching roll,pitch,yaw,thrust or p,q,r (offboard: check which topic carries them).
- param / sag: first parameter_update after intended (needs SDLOG_PROFILE param-update logging, else the ULog
  changed-parameter record) with the new value, or for SIM_GZ_THR_SC the first change in the plant effect (actuator
  thrust/ESC) if the param message is not logged.
Output: per kind, delay = applied_us - intended_us in sim steps (step = 4 ms physics, 10 ms ATTITUDE, take the
step from run.json), histogram and p50/p95/max, count of unmatched rows, and cross-run comparison of the
distribution (same scenario/seed, n runs) to quantify jitter. Rows that match several samples use the first one.
## Unverified
- Nothing executed against PX4/gz; MAVLink ATTITUDE rate/time base assumed as in the original runner.
- Whether set_param effects appear in the ULog under the current SDLOG_PROFILE.
- That `../../..` REPO also holds in the container mount (PX4_INDI_REPO can override).
