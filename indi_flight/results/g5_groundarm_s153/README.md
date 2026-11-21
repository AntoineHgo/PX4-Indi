# S153 ground-arm probe (G5.2 / G5.4, commit 1c838f4801)

Arm on the ground in ALTCTL / POSCTL (MAV_CMD_DO_SET_MODE first, throttle stick low streamed before and through the arm, no take-off
command). Phases: low 3 s, centre 5 s, climb stick (+1 m/s) until estimate altitude 3 m, centre 5 s, NAV_LAND. Runner option
`--ground-arm` (scenario `stick_ground_arm`), check script `indi_flight/bench/groundarm_check.py`, reproduce with `fly.sh` (seed 1,
quad5in, speed 4, sim v2, gps/gnss delay 110, INDI params `g5_g510_s150/params_tb03.params`). Per-run details: `*/check.json`, `*.check.txt`.

SITL binary: `build/px4_sitl_default/bin/px4` was stale (older than the 03:52 edit of McIndiPosControl.cpp); rebuilt in Docker
(`make px4_sitl_default`, 711 steps) before the flights, so it contains 1c838f4801.

| flight | max alt low / centre (m) | max thrust low / centre | landed->not-landed edge | edge step (% hover 0.137) | max alt, overshoot over 3 m | tilt > 10 deg |
|---|---|---|---|---|---|---|
| INDI altctl | 0.00 / 0.00 | 0.0014 / 0.0014 (indi_pos_status.thrust) | 40.75 s (8.6 s after arm, in climb phase) | 7.2 % (7.5 % vehicle_thrust_setpoint) | 3.34 m, +0.34 m | none (max 0.15 deg) |
| INDI posctl | 0.00 / 0.00 | 0.0014 / 0.0014 | 40.77 s (climb phase) | 7.1 % (7.4 %) | 3.32 m, +0.32 m | none (max 2.6 deg) |
| PID altctl | 0.00 / 0.00 | 0.0010 / 0.0010 (vehicle_thrust_setpoint) | 41.16 s (climb phase) | 6.1 % | 3.35 m, +0.35 m | none (max 0.03 deg) |

Land detector (INDI altctl; the other two are alike): landed, maybe_landed, ground_contact all 1 from the start (22.9 s); all clear at the
edge (ground_contact 10-25 ms later); touchdown after NAV_LAND: ground_contact 55.6 s, maybe_landed 55.9 s, landed 56.3 s.
Edge times for the other flights: see check.txt.

Verdict: no lift-off and no hover thrust while landed (low and centre) in all three; take-off with the stick is clean, edge step 6-7.5 % of
hover, under the 10 % G5.4 limit (limit not changed). Overshoot 0.3 m is the run's own: the climb stops on the estimate reaching 3 m, then the stick is centred.

Unverified / notes: single seed per case; the first ~0.2 s of `indi_pos_status` is not logged, so the max over the low phase excludes it
(vehicle_thrust_setpoint, logged from the start, gives the same max). Hover = median collective in the hold phase. The stock PID run
confirmed stock by the absence of INDI params in `params_applied` and of `indi_pos_status` in the log, not from a module list. Arming was accepted
with the stick low; whether PX4 would also accept it with the stick elsewhere was not tested. `run_scenario.py` printed "METRICS FAILED: no scenario window"
in the stdout (post-processing needs a scenario window, which this run type does not have); the flight and ulog are fine.
