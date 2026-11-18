# A-40: cause of the 70.3 s descent in g3_stick_s114

Runs: `indi/flight.ulg`, `pid/flight.ulg` (scenario stick_zsine_o6, stabilized stick mode). Clock: PX4 timestamp, same clock as run.json.

## Finding: the premise does not hold in the logs

No descent, failsafe or landing happens at 70.3 s in either run. The vehicle holds altitude through the stick phase, and the landing is commanded by the runner at 83.45 s, after the scenario window has closed.

## (1) What commands the landing

Timeline from run.json (identical in both runs, +/- 0.03 s):

| event | INDI | PID | source |
|---|---|---|---|
| offboard/stabilized switch sent (`t_offboard_us`) | 52.45 s | 52.47 s | run.json |
| window start (offboard + 3 s settle) | 55.45 s | 55.47 s | run.json `t_window_start_us` |
| stick profile start (`stick.t0_us`) | 58.45 s | 58.47 s | run.json |
| stick profile end (18 s, ZSINE_O6 duration) | 76.45 s | 76.47 s | run.json + scenarios.py |
| hold end = window end | 79.45 s | 79.47 s | run.json `t_window_end_us` |
| runner recover (4 s, sticks neutral) | 79.45-83.45 s | 79.47-83.47 s | run_scenario.py `sim.run(4.0, ...)` |
| MAV_CMD_NAV_LAND (cmd 21) | 83.45 s | 83.47 s | ulg vehicle_command |
| vehicle_status nav_state 18 (AUTO_LAND) | 83.47 s | 83.48 s | ulg vehicle_status |
| land_detected ground_contact / maybe_landed / landed | 92.84 / 93.20 / 93.54 s | 92.52 / 92.88 / 93.22 s | ulg vehicle_land_detected |
| disarm (nav_state 15 back, arming_state 1) | 95.55 s | 95.22 s | ulg vehicle_status |

- Commander log order (px4.log, no timestamps): `Landing at current position`, `Landing detected`, `Disarmed by landing`. These follow the cmd 21 at 83.45 s.
- The runner's land stage (run_scenario.py ~line 1017) sends `sim.cmd(21, ...)` unconditionally after the recover segment. This is the only landing command in the logs.
- Failsafe: no failsafe nav state and no failsafe action. `failsafe_flags` has only the `mode_req_*` and `*_invalid` bits, first true at ~13 s (arming), unchanged through the stick phase. Their exact meaning was not checked against PX4 source.
- Throttle stick (manual_control_setpoint.throttle, 0.5 s samples): swings between about -0.69 and +0.04 with a 4 s period from 60 to 75 s (ZSINE_O6), then sits at 0.000 (neutral = hover thrust) from 76.5 s. Samples at 70.0 s = -0.44, 70.5 s = +0.004. The sticks.csv applied value at 70.206 s = -0.256 (descending demand -0.58 m/s). This is the normal down-swing of the z-sine, not a land command. Stick values match in both runs.
- Local position z (up, m), 1 s samples, 60-83 s: INDI oscillates 5.5 to 7.7 m (peak at 70 s = 7.4 m, not a descent); PID 5.1 to 7.3 m. Descent to ground starts at 84 s (after cmd 21).

## (2) Set-up fault or controller behaviour

Neither. The 70.3 s descent does not exist in the logs. The only descent is the runner's NAV_LAND at 83.45 s, which is the intended end-of-scenario land (4 s after the window closes at 79.45 s). The z-sine stick swing about hover is the scenario working as designed. The 70.3 s number itself is not supported by run.json, ulg or px4.log; the README line "nav 18 at 70.3 s" and "ground at ~70.3 s" is wrong (nav 18 is at 83.47 s).

Side observation (not A-40): in the stick phase the altitude sits about 1.5 m above the 5 m hold (mean about 6.5 m, range 5.1 to 7.7 m). Not investigated further here.

## (3) Suggested fix (documentation only, no code change)

Correct the A-40 premise: in `indi_flight/results/g3_stick_s114/README.md`, replace the "70.3 s" ground/nav-18 times with the ulg values (NAV_LAND cmd 83.45 s, touchdown about 93.5 s, disarm about 95.5 s), then close A-40 as "no early descent; runner lands after window end".

## Unverified

- Exact meaning of `mode_req_*` / `*_invalid` failsafe_flags bits (only checked that they do not change at 70 s).
- nav_state 15 switch time from the ulg (my filter hid pre-55 s changes); 52.45 s is taken from run.json.
- Origin of the 70.3 s figure (not found in any file under g3_stick_s114; closest is the sticks.csv down-swing at 70.2 s).
