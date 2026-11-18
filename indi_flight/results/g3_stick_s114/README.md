# G3 stabilized stick check, S114 (centre stick = hover thrust fix, commit 807fd6a08a)

Scenario identical to g3_single_s113 (stick_zsine_o6, quad5in, v2, 800 Hz, seed 768592122, sim-seed 680969658, stabilized stick mode, base params quad5in_indi_g1.params). Run one after the other. Raw logs (flight.ulg, px4.log, csv) are untracked.

## Commands

```
indi_project/docker/run.sh -n g3s_indi -t 900 -- python3 indi_flight/bench/run_scenario.py --scenario stick_zsine_o6 --controller indi --model quad5in --sim v2 --rate-hz 800 --seed 768592122 --sim-seed 680969658 --out indi_flight/results/g3_stick_s114/indi --params indi_flight/bench/params/quad5in_indi_g1.params --stick-mode stabilized

indi_project/docker/run.sh -n g3s_pid -t 900 -- python3 indi_flight/bench/run_scenario.py --scenario stick_zsine_o6 --controller pid_default --model quad5in --sim v2 --rate-hz 800 --seed 768592122 --sim-seed 680969658 --out indi_flight/results/g3_stick_s114/pid --params indi_flight/bench/params/quad5in_indi_g1.params --stick-mode stabilized
```

Stray g3s containers before the runs: none. Both runs exited 0.

## Results

Times are on the raw PX4 timestamp clock (the same clock as run.json `t_offboard_us`); nav_state 15 switch at 52.02 s in both runs, which matches the 52 s switch in S113. Thrust is `vehicle_thrust_setpoint.xyz[2]` (NED, so negative is up; magnitudes shown as the mean value).

| run | exit / error / watchdog | hover_thr_used | alt GT 50 / 52 / 53 / 55 / 60 s (m) | alt min / max after 52 s (m) | thrust mean 50-52 s | thrust mean 52-55 s | nav 15 switch | verdict |
|---|---|---|---|---|---|---|---|---|
| indi | ok / none / none | 0.13668 | 4.98 / 5.00 / 5.00 / 5.00 / 5.61 | -0.01 / 7.93 | -0.1367 | -0.1367 | 52.02 s | flies |
| pid (pid_default) | ok / none / none | 0.13668 | 5.02 / 5.01 / 4.99 / 4.97 / 5.48 | -0.01 / 7.66 | -0.1366 | -0.1367 | 52.02 s | flies |

Notes:
- The min of -0.01 m in both runs is the touchdown at the end of the flight. Both px4.log files show `Landing at current position`, `Landing detected`, `Disarmed by landing` (commander, nav_state 18 at 70.3 s). No failsafe message is logged, so the cause of the landing at 70 s, which is in the stick phase, is not explained by these logs and needs checking.
- The altitude max of 7.9 m (INDI) and 7.7 m (PID) after the switch means the stick phase swings about 3 m above the 5 m hold altitude in both controllers.
- Thrust after the switch equals hover_thr_used (0.1367), so the centre-stick hover thrust fix holds: the 0.137 -> 0.095 step seen in S113 does not happen.

## Verdict

- indi: flies. The vehicle holds through the 52 s switch to STABILIZED (nav 15), no fall.
- pid_default: flies. Same behaviour, no fall through the switch.
