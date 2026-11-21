# G5.10 SAT set-up check (S181), read-only, from indi_sat_s1 and pid_sat_s1 logs

1. Injection at 4.96 m (INDI) / 4.99 m (PID) truth altitude, hovering, command 0.137. Manoeuvre: position step +3.0 m x (north, no z change, no yaw) at the same instant as the thrust scale step 1.0 -> 0.136.
2. Motors were NOT commanded to full scale at injection: the controller still sent the hover command 0.137 (thrust setpoint 0.137), nothing limited it. It rose only as the position/altitude loop reacted (INDI 0.21 at +0.1 s, 0.58 at +0.4 s, 0.90 at +0.8 s, 1.00 at +1.2 s; PID 0.16, 0.34, 0.62, only 0.86 at +1.3 s). MPC_THR_MAX 1.0, MPC_THR_MIN 0.05, nav_state 14 (offboard) throughout, land detector never set (landed, freefall, ground_contact all 0) so none of those limited it. Max command 1.0 (INDI) only after the vehicle was already at 1.3 m going down at 4.5 m/s.
3. Max rotor speed (esc_status, rpm of the 4 motors): INDI 9528 rpm at command 1.0, PID 9171 rpm (never above 0.86 command). Expected sqrt(0.136) * nominal max = 0.369 * 2700 rad/s = 996 rad/s = 9508 rpm. INDI matches (+0.2 %), so the scale reaches the sim and is applied once. Hover before injection was 9542 rpm at command 0.137 (= 2700 * sqrt(0.137)), so hover after injection needs 1.007 command -> 9542 rpm > 9508 available: thrust/weight 0.993.
4. The fall is NOT thrust/weight 0.99. It is a set-up fault of the step form: the plant loses 86 % of its thrust in one step (SIM_GZ_THR_SC 0.136 applied at 58.19 s INDI / 58.675 s PID, i.e. 0.05 s after segment start, via the single atomic SIM_GZ_THR_SC param, not EC_MIN/MAX; no double scaling, EC_MIN/MAX unchanged at 0/2700 in the log, README/fault_apply text about EC is outdated for the uniform case). Rotor speed dropped from 9540 to 5400-4800 rpm within 0.1-0.2 s (thrust/weight ~0.14 -> near free fall, vz -0.87 m/s at +0.2 s, -2.4 m/s at +0.5 s), and the controller needs about 1.2 s (INDI) to wind the command from 0.137 to 1.0, during which the vehicle sinks 3.5 m; then it is at 1.3 m with 4.5 m/s down speed and thrust/weight 0.99 cannot stop it (impact at +1.6 s, vz -3.5 m/s; PID at +1.4 s, -6 m/s). Contributing: the 3 m step tilts the vehicle to 59 deg (INDI) / 39 deg (PID) while T/W <= 1, tilt costs vertical thrust; and altitude 5 m is small (any 1.2 s of near free fall = 7 m). Motors >= 0.99 for 0.51 s is only the last 0.5 s before impact. This is a G3-type thrust-loss probe, not sustained saturation; no controller can meet "alt loss <= 2 m" in it.
5. Recommendation: reach saturation from a hover that is already at the limit: apply the scale during settle (or ramp it over several seconds while the controller adapts) so the hover command is ~1.0 (MPC_THR_HOVER ~0.99 / hover estimate follows) before the step, drop the 3 m step to a small one (<= 0.5 m, tilt costs altitude at T/W 0.99), and fly at >= 10 m altitude.

## Tables (10 Hz source, shown 0.1-0.2 s steps around injection; t=0 is the sat segment start, alt = -z of vehicle_local_position_groundtruth)
INDI (sat start 58.14 s, ulog param change 58.194 s): t, alt m, vz (up) m/s, spz m, spx m, thrust sp, motors min/max, rotor rpm max/min (esc_status 0), tilt deg
- -2.0..0.0: 4.96, -0.00, 4.96, 0.00, 0.137, 0.136/0.137, 9542/9528, 0.1-0.5 deg
- +0.1: 4.95, -0.17, 4.96, 3.00, 0.210, 0.173/0.248, 5942/5471, 0.5
- +0.2: 4.90, -0.87, 4.96, 3.00, 0.329, 0.306/0.352, 5385/4942, 4.2
- +0.4: 4.61, -1.97, 4.96, 3.00, 0.579, 0.575/0.584, 7000/6985, 25
- +0.6: 4.12, -2.83, 4.96, 3.00, 0.814, 0.792/0.837, 8500/8271, 49
- +0.8: 3.48, -3.65, 4.96, 3.00, 0.903, 0.879/0.928, 9157/8928, 59
- +1.0: 2.67, -4.33, 4.96, 3.00, 0.932, 0.915/0.952, 9257/9042, 52
- +1.2: 1.77, -4.55, 4.96, 3.00, 1.000, 0.962/1.000, 9500/9342, 30
- +1.4: 0.87, -4.47, 4.96, 3.00, 1.000, 0.950/1.000, 9500/9314, 2
- +1.6: 0.02, -3.54 (impact), 1.000, 0.191/0.987, 9528/9157, 18
PID (sat start 58.628 s, param change 58.675 s; setpoint z 5.00)
- -2.0..0.0: 4.97-4.99, +0.01, 0.137, 0.136/0.137, 9571/9528, <0.2 deg
- +0.1: 4.99, -0.19, thrust 0.163, 0.123/0.203, 5500/5157, 0.1
- +0.2: 4.93, -0.95, 0.216, 0.177/0.256, 4800/3757, 5
- +0.4: 4.60, -2.37, 0.341, 0.294/0.388, 5685/5057, 32
- +0.6: 3.98, -3.76, 0.477, 0.450/0.504, 6628/6142, 37
- +0.8: 3.12, -4.74, 0.616, 0.596/0.648, 7442/7185, 20
- +1.0: 2.11, -5.37, 0.760, 0.745/0.775, 8300/8085, 14
- +1.2: 0.99, -5.78, 0.838, 0.818/0.857, 8728/8571, 20
- +1.4: 0.00 (impact, watchdog height<0.3 m at sim t 59.97), vz -5.95 before
Both: nav_state 14 throughout, land detector flags all 0, xy setpoint steps to x=+3.0 at t=+0.1 s.
Parameter log: only SIM_GZ_THR_SC 1.0 -> 0.136 (INDI 58.194 s, PID 58.675 s); SIM_GZ_EC_MIN*/MAX* never changed (MIN 0, MAX 2700).
