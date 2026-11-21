# G4 chatter cause search (S178, log analysis only)

Script `bench/chatter_chain_s178.py` (host python3, pyulog+numpy), self-test `bench/tests/test_chatter_chain_s178.py` (ok). Logs: `g4/cruise_typ_s1`, `g4/cruise_harsh_s2` (harsh agrees with typ unless noted), PID ref `g4_gate_s169/pid_cruise_typ_s1`. Full per-signal tables: run the script on the three `flight.ulg`.
Method: Welch 2 s Hann (1.5 s / 1.0 s in the short L2 windows), peak in the line band over median PSD 20..min(100, 0.9 Nyq), plus line RMS +-1 Hz in native units. Ratios on noise-free signals (setpoints, estimator) are huge and not comparable: compare INDI with PID by line RMS.

## Logged rates (Nyquist)
800 Hz: actuator_motors, thrust/torque_setpoint, indi_rate_status, gyro, esc_status (782, rpm of 4 motors). 267: rates_setpoint, vehicle_acceleration, vehicle_attitude. 89 (Nyq 44.5): indi_pos_status, vehicle_local_position(_setpoint), attitude_setpoint; 33 Hz is resolvable there but cannot be told from aliases (55.6 / 70.3 Hz). **trajectory_setpoint is logged at 42.8 Hz (Nyq 21): it cannot show 33 Hz** (its dt is the sender period, see L1).

## L1, 33.5 Hz, lemniscate window 38-52 s (line RMS, typ_s1 INDI / PID)
| signal | INDI | PID | note |
|---|---|---|---|
| trajectory_setpoint dt | 30.0 ms (33.3 Hz) | same sender | the line frequency |
| lpos_setpoint x, y [m] | 9.0e-3 / 8.8e-3 | 6.9e-3 / 7.6e-3 | staircase, same in both |
| lpos measured x, vx; gyro; attitude | no line (x1-12) | no line | vehicle does not follow it |
| a_c horizontal [m/s2] (= t_c[0,1]) | 6.5e-2 (x197) | 1.5e-2 (lpos_sp accel, x153) | 4x; harsh 5.6e-2 |
| a_f, t_f, a_c[2], t_c[2] | x1 | - | no vertical line, none in filtered force |
| thrust norm / att_sp thrust_body | 6.3e-4 (x305) | 2.0e-4 (x121-340) | 3x = the "3x floor" |
| actuator_motors collective | 6.1e-4 (x1059) | 2.0e-4 (x340) | carries the line |
| motors diffA / B / C | 6.8e-6 / 1.3e-4 / 8.9e-5 | 9e-7 / 1.7e-5 / 1.2e-5 | 5-90x below collective |
| esc rpm collective | 2.9 rpm (x184) | 1.0 (x18) | rotors follow |

Upstream point: the offboard setpoint staircase at 33.3 Hz in the horizontal setpoint (position with velocity/acceleration feed-forward steps), also in the PID flight at 1/3 to 1/4 the motor amplitude. It enters the horizontal a_c (tilt path); the collective shows it because the thrust magnitude |t_c| projects a horizontal line onto thrust when mean horizontal acceleration is non-zero (not an independent vertical line: a_c[2], t_c[2] have none; order-of-magnitude argument only).
Why INDI is 3-4x: INDI xy gains are 2x stock (MC_INDI_XY_P 1.9 vs MPC_XY_P 0.95, MC_INDI_XY_VP 3.6 vs MPC_XY_VEL_P_ACC 1.8; MPC_VEL_LP=0 so velocity unfiltered, both runs) and a_c goes straight into t_c: `src/lib/indi_accel_control/indi_accel_control.cpp:364` `t_c = t_f + (a_c - a_f)`, with a_f line-free so nothing cancels it. Stepped feed-forward: `McIndiPosControl.cpp:1090` (`_a_ff = setpoint.acceleration`), `:316`. Sender: `bench/run_scenario.py:104` SETPOINT_PERIOD 0.02 but the sim-time grid lands on 30 ms (comment at :477).
Most likely cause: test-rig 33.3 Hz setpoint staircase amplified by the doubled INDI outer gains; not a loop oscillation.

## L2, 18.7 Hz (detector 20-22), AUTO_LAND
The old window 65-72 mixes descent (z -4 to -0.5 m, 62-67 s, stage_mode 1, measured force) and ground (landed 68-69 s, stage_mode 2). Split into L2d 62-66.5 and L2g 69.5-72.
| signal (typ_s1) | L2d INDI | L2d PID | L2g INDI |
|---|---|---|---|
| groundtruth vx / q[1] | 6.2e-5 / 3.9e-6 | 2.9e-5 / 1.7e-6 | - |
| EKF vx [m/s] | 2.4e-3 (harsh 6e-3) | 3.6e-3 (40-60x truth) | weak (x11) |
| a_c horizontal | 3.5e-2 (harsh 9.4e-2) | 2.6e-2 | n/a |
| a_f horizontal | 2.6e-2 | - | n/a |
| rates_sp pitch / roll | 5.7e-3 | 3.1e-3 | x17 |
| gyro | 9.2e-4 (harsh 2.5e-3) | 4.1e-4 | x6 |
| torque_setpoint | 2.6e-4 (harsh 7e-4) | 1.2e-4 | x4 |
| motors diffB / diffC | 2.0e-4 / 1.8e-4 (harsh 5.4e-4 / 5.0e-4) | 8.5e-5 / 8.5e-5 | x4-6 |
| motors collective | 2.5e-5 (22 Hz) | 2.4e-5 | 2e-6 |
| esc rpm diffB / C | 1.6 / 1.4 (harsh 3.4 / 3.1) | 0.8 / 0.5 | 0.4 |
Findings: attitude channels (diffB/C, torque), not collective. The 18.7 Hz line exists in the PID flight in the same descent window (INDI motors 2.4x typ, 6x harsh larger) and in the physical truth (tiny), so it is a shared descent excitation; the INDI-specific part is amplification (a_c 1.3x typ / 3.6x harsh vs PID, gyro-to-torque 2-4x). On the ground (L2g) the motors have no line (x3-6): the flag is the descent, 1-2 s after nav_state 18; no land-detector branch fits (blend/stage_mode constant until 68.8 s). Most upstream resolvable point: EKF horizontal velocity/acceleration (lpos vx, ax), 40-60x the true line, also in PID; it enters the INDI P/D at `McIndiPosControl.cpp:601` (`MC_INDI_XY_VP` 3.6, 2x stock) with no velocity filter (:506, MPC_VEL_LP=0) and MPC_VELD_LP 5 Hz (:513).
Most likely cause (moderate confidence): estimator velocity line (origin unknown) fed straight to the doubled, unfiltered xy velocity P gain.

## Proposed probe (one flight, not run)
cruise_typ_s1, same seed, with `MPC_VEL_LP=8` and the runner sender at 10 ms (`SETPOINT_PERIOD=0.01`, this run only). The lines are in disjoint windows (L1 38-52, L2 62-66.5). Expect L2d motors diffB/C 18.7 Hz line RMS to fall from 2.0e-4 toward the PID 8.5e-5, and the L1 33.3 Hz line to vanish from motors collective. If L1 persists the sender is not the cause; if L2 does not fall the EKF line is not entering through the velocity P path (then try MC_INDI_XY_VP=1.8).

## Unverified
- Origin of the 18.7 Hz EKF velocity line (also in PID); 89 Hz topics cannot exclude aliases (70.3 / 55.6 Hz). a_f horizontal 2.6e-2 is larger than sensor_accel x tilt would give (not reconciled; interpolation over indi_pos_status gaps, 5631 of 6501 samples, possible).
- Causality (setpoint-driven vs loop oscillation) rests on the PID comparison and on no line in measured position/attitude at L1. Only typ_s1 and harsh_s2 analysed, single PID seed, 0.5 Hz bins.
- The thrust-projection explanation is not computed from the log.
