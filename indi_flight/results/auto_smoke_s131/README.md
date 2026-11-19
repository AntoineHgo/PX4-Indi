# S131 AUTO smoke flights, INDI position module on, quad5in, seed 1

Both flights: exit ok, runner error None. `auto_tour` and `auto_land10`, params file `params.params` (copy of the S129 file:
quad5in INDI defaults + `MC_INDI_POS_EN 1`, `MC_INDI_EN 1`, `MC_RATE_CTL_TYPE 1`). Raw `flight.ulg` untracked (gitignored).

Commands (serial, inside the container, wall timeout):

    timeout 600 indi_project/docker/run.sh -n s131tour -t 500 -- python3 indi_flight/bench/run_scenario.py --scenario auto_tour --controller indi --model quad5in --seed 1 --speed 4 --sim v2 --params indi_flight/results/auto_smoke_s131/params.params --out indi_flight/results/auto_smoke_s131/auto_tour
    (same with --scenario auto_land10 --out .../auto_land10)
    python3 indi_flight/bench/auto_smoke_check.py indi_flight/results/auto_smoke_s131/auto_tour --json .../check.json

## Flags
- Take-off handover thrust step is NOT measurable from `indi_pos_status.thrust`: the first `indi_pos_status` sample is 0.10 s (tour) and 0.18 s (land10) AFTER the takeoff_status rampup->flight edge, so there is no sample before the edge. Step of `vehicle_thrust_setpoint` (-xyz[2], the thrust command whoever publishes it) at the edge: 0.035 in both runs (hover thrust of the stock default not known here). Altitude dip within 1 s after the edge: 0.000 m (the vehicle is still climbing at the edge, 4 m/s^2 ramp).
- stage_mode is 1 (indi) in every sample of both flights, no transition.
- `metrics.json` says "METRICS FAILED: no scenario window" for both runs (offboard-based metrics, not applicable to AUTO); ignore, use `check.txt`.
- MIS_TAKEOFF_ALT set through the param CLI right before `commander takeoff` did not reach the navigator (first try: "Using default takeoff altitude: 5.0 m" for a 10 m scenario, climb stuck at 5 m). The runner now passes the AMSL altitude in the takeoff command (param 7). Cause of the param not taking effect UNVERIFIED.
- Mission start was first "denied! No valid mission" right after the upload ack; the runner now waits 2 s then retries (it needed 1 try, run.json `mission_start_tries`).
- Tracking error is the ground truth (`vehicle_local_position_groundtruth`) against the finite `trajectory_setpoint` position rows; in the mission the xy error (0.49 m rms) is dominated by the lag against a moving setpoint, it is not a hold error.
- Landing: mean vz 0.709 / 0.697 m/s (down, 1-4 m height) against MPC_LAND_SPEED 0.70. Ground contact to disarm 2.7 s (landed to disarm 2.0 s = COM_DISARM_LAND).

## auto_tour check output
```
scenario auto_tour exit ok error None
phases (sim s): armed=31.2, takeoff_cmd=31.2, takeoff_done=39.4, hold_end=49.4, mission_uploaded=49.4, mission_start=51.4, mission_end=75.7, rtl_cmd=78.7, disarmed=95.2

== tracking vs trajectory_setpoint (ground truth; rows with finite position setpoint only)
takeoff  [31.2,39.4] n=411 xy rms 0.026 max 0.040 m | z rms 0.142 max 0.229 m
hold     [39.4,49.4] n=500 xy rms 0.033 max 0.056 m | z rms 0.041 max 0.112 m
mission  [51.4,75.7] n=1215 xy rms 0.491 max 0.790 m | z rms 0.055 max 0.096 m
rtl      [78.7,95.2] n=824 xy rms 0.130 max 0.220 m | z rms 0.098 max 0.544 m

== take-off handover (takeoff_status rampup(4) -> flight(5))
edge at 34.252 s: indi_pos_status.thrust step nan (nan = no sample before the edge; first sample 34.354 s), altitude dip within 1 s 0.000 m
vehicle_thrust_setpoint (-xyz[2]) step at the edge: 0.0347

== landing
ground_contact 91.66 s, landed 92.33 s, disarm 94.34 s -> contact->disarm 2.68 s (landed->disarm 2.01 s)
mean vz (down+) between 1 and 4 m height: 0.709 m/s over 385 samples; MPC_LAND_SPEED 0.699999988079071

== stage_mode / nav_state transitions
indi_pos_status stage_mode: first 1 at 34.35 s, n=5094, values [1], transitions []
vehicle_status nav_state: [(31.23, 'loiter', 'takeoff'), (37.81, 'takeoff', 'loiter'), (51.45, 'loiter', 'mission'), (75.71, 'mission', 'loiter'), (78.75, 'loiter', 'rtl'), (94.34, 'rtl', 'loiter')]
heartbeat mode_log [t, main, sub, armed]: [[32.212, 4, 2, True], [38.208, 4, 3, True], [52.212, 4, 4, True], [76.211, 4, 3, True], [79.211, 4, 5, True], [95.208, 4, 3, False]]
```

## auto_land10 check output
```
scenario auto_land10 exit ok error None
phases (sim s): armed=31.2, takeoff_cmd=31.2, takeoff_done=42.6, hold_end=52.6, land_cmd=52.6, disarmed=69.1

== tracking vs trajectory_setpoint (ground truth; rows with finite position setpoint only)
takeoff  [31.2,42.6] n=572 xy rms 0.045 max 0.081 m | z rms 0.191 max 0.281 m
hold     [42.6,52.6] n=500 xy rms 0.029 max 0.053 m | z rms 0.038 max 0.118 m
land     [52.6,69.1] n=829 xy rms 0.040 max 0.072 m | z rms 0.102 max 0.541 m

== take-off handover (takeoff_status rampup(4) -> flight(5))
edge at 34.178 s: indi_pos_status.thrust step nan (nan = no sample before the edge; first sample 34.358 s), altitude dip within 1 s 0.000 m
vehicle_thrust_setpoint (-xyz[2]) step at the edge: 0.0346

== landing
ground_contact 65.51 s, landed 66.19 s, disarm 68.20 s -> contact->disarm 2.69 s (landed->disarm 2.01 s)
mean vz (down+) between 1 and 4 m height: 0.697 m/s over 380 samples; MPC_LAND_SPEED 0.699999988079071

== stage_mode / nav_state transitions
indi_pos_status stage_mode: first 1 at 34.36 s, n=2770, values [1], transitions []
vehicle_status nav_state: [(31.17, 'loiter', 'takeoff'), (41.06, 'takeoff', 'loiter'), (52.59, 'loiter', 'land'), (68.2, 'land', 'loiter')]
heartbeat mode_log [t, main, sub, armed]: [[31.151, 4, 3, True], [32.148, 4, 2, True], [41.152, 4, 3, True], [53.152, 4, 6, True], [69.15, 4, 3, False]]
```
