# S131 AUTO land10 reference flight, stock position controller (PID)

Same as the S131 `auto_land10` flight except `MC_INDI_POS_EN 0` (`params.params` = S131 copy with only that line changed; INDI inner loop unchanged, `MC_INDI_EN 1`, `MC_RATE_CTL_TYPE 1`). Seed 1, quad5in, exit ok, runner error None. Raw `flight.ulg` untracked (gitignored). `run_stdout.txt` holds the runner stdout.

Command (serial, inside the container, wall timeout):

    timeout 600 indi_project/docker/run.sh -n s131pidland -t 500 -- python3 indi_flight/bench/run_scenario.py --scenario auto_land10 --controller indi --model quad5in --seed 1 --speed 4 --sim v2 --params indi_flight/results/auto_smoke_s131_pid/params.params --out indi_flight/results/auto_smoke_s131_pid/auto_land10
    python3 indi_flight/bench/auto_smoke_check.py indi_flight/results/auto_smoke_s131_pid/auto_land10 --json indi_flight/results/auto_smoke_s131_pid/check.json > indi_flight/results/auto_smoke_s131_pid/check.txt

`--controller indi` is kept from S131 (the runner's flag); the flight used stock position control because `MC_INDI_POS_EN 0`. Check the runner's `--controller` handling if this matters for the comparison.

## Comparison (PID this flight vs INDI S131 land10)

| Metric | PID (this flight) | INDI (S131) |
|---|---|---|
| vehicle_thrust_setpoint (-xyz[2]) step at takeoff rampup(4) -> flight(5) edge | 0.0075 (edge 34.08 s) | 0.0347 (edge 34.178 s) |
| Altitude dip within 1 s after edge | 0.000 m | 0.000 m |
| Mean landing vz, 1-4 m height (down+) | 0.704 m/s (378 samples) | 0.697 m/s (380 samples) |
| Ground contact -> disarm | 2.70 s | 2.69 s |

Caveats:
- The checker's handover block prints "missing takeoff_status / indi_pos_status" for this flight (`indi_pos_status` has no samples with `MC_INDI_POS_EN 0`), so `check.txt` has no handover numbers. The PID step and dip above come from an inline snippet using the same takeoff_status edge (4 -> 5) and the same `handover_metrics` windows, not from the checker.
- The edge is the takeoff_status ramp edge as in S131. For PID it is 34.08 s, and the PID thrust step is much smaller, so the INDI thrust step is not directly comparable with PID.

## Step definition in the checker

`indi_flight/bench/auto_smoke_check.py:19-24`: step = |mean(thrust in [t_edge, t_edge+w)) - mean(thrust in [t_edge-w, t_edge))| with w = 0.05 s (default at line 19). It is a 50 ms mean on each side of the edge, not an instantaneous sample difference and not a 0.1 s window. The vehicle_thrust_setpoint trace is used for the S131 and PID numbers (line 111-114).

## check.txt
See `check.txt` (checker stdout, also `check.json`).
