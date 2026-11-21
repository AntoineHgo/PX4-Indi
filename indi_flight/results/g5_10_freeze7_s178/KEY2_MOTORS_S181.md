key2 score_motors: DISAGREE (6 items)

# KEY2 G5.10 motor-saturation metrics (S181)

Script: indi_flight/bench/g510_motors_key2.py; self-test: indi_flight/bench/tests/test_g510_motors_key2.py (run: `python3 <file>`, 3 tests ok incl. known 2.5 s saturation, known 0.973 s attitude recovery, break check thr 1.01 -> 0).

## Signals and time base (checked in the four ULogs)
- actuator_motors 800 Hz, truth attitude/position ~690 Hz: timestamp_sample (equals timestamp, median lag 0 in all four logs). manual_control_setpoint ~46 Hz: timestamp_sample. vehicle_attitude_setpoint 89 Hz: only timestamp exists. Truth interpolated to the setpoint samples, no hold of decimated topics. ULog time = sim time (events in run.json).
- Params from the log: MPC_MAN_TILT_MAX 35 (stab limit 40), MPC_TILTMAX_AIR 45 (sat limit 50).
- Saturated = commands >= 0.99; 'all4' = all four motors, 'any' = at least one. Windows from run.json events: sat = [sat, sat+5 s], stab = [full, full+1 s]. Stick centre = first manual_control_setpoint sample after the last non-zero roll/pitch/throttle. Attitude error = quaternion angle truth vs q_d of vehicle_attitude_setpoint. LOC = truth height < 0.3 m or tilt > 90 deg.

## Results (key2)
| flight | sat all4 s | sat any s | tilt max / limit | alt loss m | LOC | recovery | pass |
|---|---|---|---|---|---|---|---|
| indi_sat_s1 | 0.0000 (of 1.59 s logged) | 0.5100 | 58.92 / 50 | 4.94 | True | not reached (log ends 59.67 s, crash) | FAIL |
| pid_sat_s1 | 0.0000 (of 1.40 s logged) | 0.0250 | 39.50 / 50 | 4.99 | True | not reached (log ends 59.95 s, crash) | FAIL |
| indi_stab_s1 | 0.7697 (of 1.00 s logged) | 0.9835 | 35.52 / 40 | n/a (max gain 472 m) | False | att err stays <=5 deg from 0.240 s after centre (t_c 59.144); err at +1 s 0.15 deg | PASS |
| pid_stab_s1 | 0.7592 (of 1.00 s logged) | 0.9830 | 34.99 / 40 | n/a (max gain 475 m) | False | att err stays <=5 deg from 0.244 s after centre (t_c 59.291); err at +1 s 0.86 deg | PASS |

Sat flights: both fell to the ground ~1.5 s after the injection (watchdog height < 0.3 m at 59.67 / 59.97 s; truth crash 59.668 / 59.946 s), so the Q9 c check 'motors sit >= 0.99' is NOT met (all4 0 s; any 0.51 s INDI, 0.025 s PID of 5 s) and the 5 s saturation never ran. INDI sat tilt 58.9 deg > 50.

## Comparison with key 1 (score_motors.py, run by key2 on the four flights; its .motors.json outputs did not exist)
| item | key1 | key2 | verdict |
|---|---|---|---|
| stab sat time all4 INDI / PID | 0.7713 / 0.7613 s | 0.7698 / 0.7593 s | agree (0.2-0.3 %) |
| stab sat time any INDI / PID | 0.985 / 0.985 s | 0.9835 / 0.983 s | agree (0.2 %); key1 window is 1.001 s (full..rec) vs 1.000 |
| stab tilt max, alt loss, alt gain | 35.519 / 34.990, 0, 472.2 / 475.5 | same | agree |
| stab recovery | level (tilt<=5 deg) 0.235 / 0.236 s after last motor>=0.99 sample | err to q_d stays <=5 deg from 0.240 / 0.244 s after stick centre | numbers agree (2-3 %) but definitions differ, see D3 |
| stab LOC / pass (item 1, item 2) | loc True, pass_limits False both | LOC False, PASS both | DISAGREE: key1 defect D1 |
| stab tilt limit (item 3) | 50 deg (MPC_TILTMAX_AIR+5) | 40 deg (MPC_MAN_TILT_MAX+5) | DISAGREE: key1 defect D2 (no verdict change, 35.5 < 40) |
| sat (items 4, 5: both flights) | script crashes KeyError 'rec' at line 20 | numbers above | DISAGREE: key1 defect D4 |

## Defects (all in key1 score_motors.py)
- D1 line 40: `loc = ... or run.get('exit_status') != 'ok'`. run.json exit_status is 'failed' in both stab runs because of a wall timeout in the LAND phase at sim t=668 s / 658 s, 10 minutes after the 13 s scored window; truth height min 5.0 m, tilt <= 35.5 deg. This flags LOC and makes pass_limits False wrongly. Key2 is right (no LOC).
- D2 lines 37, 40-41: stab tilt limit uses MPC_TILTMAX_AIR + 5 = 50 deg; Q17 A (GATES.md S180) says MPC_MAN_TILT_MAX + 5 = 40 deg. Also line 41 applies the 2.0 m alt-loss limit that Q17 A removes (no effect here, loss 0).
- D3 lines 33-35, 44-46: recovery is 'tilt <= 5 deg after the last motor >= 0.99 sample', not 'attitude error to the stick-commanded attitude <= 5 deg within 1 s of stick centre'; reference time and quantity differ (yaw ignored). The two reference times only differ by ~4 ms here, so the numbers happen to agree.
- D4 line 20: requires an 'rec' event; the aborted sat runs have only settle and sat, so the script cannot score them. It also has no tilt/LOC/alt-loss/recovery for the sat part (README says g510_check does that).
- Key2 caveats: LOC rule (height < 0.3 m or tilt > 90) is my reading, not stated in GATES.md; sat recovery needs the run to reach sat end + 5 s (not the case); sat window start from the run.json event, not from a log of the injection actually taking effect.
- Not verified: why the 0.136 scale gives free fall rather than a pinned-at-1.0 hover (hover thrust 0.137 would need 1.007; the motor model may be nonlinear), and the sim's thrust scale actually applied in the sat segment.
