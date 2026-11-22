# Q26 run 264 (G3 C3, sat 0.351 + weak motor 3 x0.709): log-only cause search (S207)

Log time = sim time (gust/fault trigger 58.683). Tilt from vehicle_attitude_groundtruth; the abort (60.9 s in the S199 note) is 60.29 s by ground-truth tilt > 60 deg
(campaign run: 60.06 s). INDI = speed-1 re-fly, PID = same draw. Host python3 + pyulog, no Docker needed.

| event (t_rel = s after the rotor dip) | INDI | PID |
|---|---|---|
| fault step + gust start, rpm of rotors drop, p/q/r kick (-91 q, -68 r) | 58.70-58.80 | 58.70 |
| hover at 0.51-0.52 (motors 0,1), 0.20 (CW 2,3 after yaw settles), 0.73-0.75 (motor 3) | 59.2-59.7 | 59.2-59.6 |
| first divergence candidate: none before the dip, motors/torques/rates equal within ~10 dps | -- | -- |
| rotor dip, esc_status rpm of motors 2,3 11600 -> ~7000 in 20 ms, motor command flat 0.20 (plant side) | 59.722 | 59.618 |
| yaw rate r kick to +142 / +128 dps (actuator command not the cause) | 59.78 | 59.66 |
| roll/pitch rate peak: INDI q 175 dps (t_rel +0.38), PID q 81 dps (+0.18) | 60.10 | 59.80 |
| rate setpoint on 220 dps limit (roll, then pitch) | 60.27 / 60.33 | never (min -118) |
| tilt > 60 deg | 60.29 | never (max 41 deg) |

Always 0: control_allocator_status unallocated_torque (all 3 axes), no motor at 0 or 1 until 60.4 s (motor 3 max 0.87 at abort). No saturation, no
yaw-vs-roll/pitch trade in the allocator. torque_setpoint_achieved stays true.

## Divergence (t_rel after dip, same disturbance in both stacks)
Both stacks get the same plant disturbance (CW pair rpm collapse -> yaw kick and about +12 rad/s2 pitch/roll accel, indi_rate_status angular_accel_filtered).
The difference is the counter-torque they apply (vehicle_torque_setpoint):

| t_rel | roll tsp INDI / PID | pitch tsp INDI / PID | q INDI / PID (dps) |
|---|---|---|---|
| +0.06 | -0.020 / -0.022 | -0.007 / -0.020 | 32 / 40 |
| +0.10 | -0.031 / -0.041 | -0.016 / -0.034 | 61 / 57 |
| +0.14 | -0.042 / -0.057 | -0.029 / -0.050 | 92 / 71 |
| +0.18 | -0.048 / -0.070 | -0.034 / -0.063 | 116 / 81 |
| +0.22 | -0.057 / -0.076 | -0.050 / -0.073 | 140 / 81 |

INDI applies 55-60 % (pitch) and 70-80 % (roll) of PID torque for 0.2 s while q is still growing; measured torque (eRPM) shows the true pitch torque
stays positive (+0.01) until +0.30 s. INDI's torque is nu = MC_INDI_K_x (20 /s) x rate error plus the increment (nu - a_f)/G1 on a measured-torque base
(torque_filtered), so the correction is a 20 rad/s2 per rad/s proportional loop against a disturbance accel of ~12 rad/s2 and error ~1.2 rad/s: nu -8 to -23 rad/s2
over the first 0.12 s (indi_rate_status nu[1]). The pitch rate then overshoots to 175 dps against a setpoint of -129 (wrong direction), the attitude
loop pushes the rate setpoint to the 220 dps limit, the vehicle rotates through (tilt 3 deg at +0.22 -> 62 deg at +0.58).

## Cause
Shown on log: the trigger is a sudden rpm collapse of the two CW rotors (both stacks, command flat, no saturation, no unallocated torque), which kicks yaw
and roll/pitch; INDI's roll/pitch rate loop (nu = 20/s x error, torque built from lagged measured torque) answers with about half of the PID torque and loses
the recovery. Likely (not shown): that loop gain/lag, not allocation or saturation, is why INDI diverges; I did not run a gain change. Hypothesis: the CW
rpm collapse itself is a gz rotor-model effect at command 0.20 with the 0.351 speed scale (sqrt) and weak motor, I did not trace it in the sim.

## Candidate fix (described only)
Raise the INDI rate-loop bandwidth on roll/pitch (MC_INDI_K_R/P from 20 toward ~35-40) or add a transient disturbance-feedforward from angular_accel_filtered;
the smallest probe is a parameter change (K_R/K_P) in a PID-twin-matched re-fly. INDI-specific: stock control_allocator is not involved (no unallocated torque).
Confidence: likely for INDI rate-loop shape, hypothesis for the dip origin.

## Scripts (host python3, from the run directory; results in g3_refly_s199/{indi,pid}_264/run_264/flight.ulg and g3_campaign_f10/run_264/flight.ulg)
- `python3 tl.py 58.6 60.4 0.1` : coarse side-by-side (tilt, motors 0-3, rpm, gt rates, rate sp, torque sp, unallocated torque)
- `python3 zoom.py` : 20 ms zoom on the rpm dip (motors, rpm, tsp, thrust, rates, measured torque, fault flag)
- `python3 aligned.py` : INDI/PID aligned on the dip onset (rates, setpoints, torque sp, INDI nu / accel / applied rate sp)
- `python3 indi_inner.py` : INDI nu, a_f, torque_filtered, increment, torque_sp, measured torque, roll and pitch
- `python3 campaign.py` : campaign run tilt>60 time and peak q
