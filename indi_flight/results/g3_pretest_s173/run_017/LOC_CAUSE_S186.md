# Run 17 INDI LOC cause (S186, log only)

Script: `indi_flight/bench/loc_timeline.py flight.ulg t0 t1 step` (timeline; all rates read: motors/rates/truth 800 Hz,
attitude 267 Hz, indi_pos 89 Hz, land detector/vehicle_status event-based, so ZOH only on those).

## Timeline (ulog s)
| t | event |
|---|---|
| 20-28 | pitch rate oscillation appears and grows (q rms 0.1 -> 4.9 rad/s, about x2 per s), saturates by 28 s at 1.8 Hz |
| 28-74 | q rms 4.7-5.0 rad/s all flight (truth gyro agrees: 4.6-4.9), tilt swings 2-64 deg; PID same phase q RMS 0.08-0.95 rad/s (1 s windows), a 2.5-3.25 Hz p/q line of 10-25 deg/s, about 25x below INDI (owner review S186) |
| 69.45 | LAND (nav 18). Descent z 4.5 -> 0 m, motors unsaturated (max 0.27), hover thrust 0.19, measured_torque_in_use=1, fault=0, torque valid 15/15, frozen 0 |
| 75.70 | first truth z < 0.05 m (touchdown during pitch limit cycle, tilt 15-34 deg) |
| 76.2-76.6 | rests on ground (tilt 0), thrust 0.05-0.07, motors min 0; indi_pos blend_frozen=1 |
| 76.68-76.74 | land detector ground_contact flickers 1 for 0.06 s, never maybe_landed/landed; indi_pos stage_mode 2 + blend_hold 1 one cycle (76.70) |
| 76.7-77.2 | vehicle lifts (z 0.05 -> 0.22), roll/pitch/yaw rate error 5-10 rad/s, tilt 16 -> 72 deg |
| 77.20 | thrust spike 0.47, 4 motors at 1.0, yaw rate err -40 rad/s |
| 77.3-78.2 | tumble, tilt up to 128 deg at 77.86, z up to 1.3 m; recovers by 79 s, lands 92.3 s |

## First divergence
Rate/attitude loop, pitch axis, from t~20 s (not the landing logic, not actuator state). Pitch is in a sustained 1.8 Hz limit cycle
(angle amplitude about 35 deg) from 28 s on; roll and yaw are quiet until touchdown. Motors not saturated, eRPM measured torque in use,
no fault flag, so not an actuator-state fault. The LOC is that limit cycle meeting the ground: touchdown at 75.7 s with the vehicle swinging,
low thrust (0.05-0.07) and motors at 0 near ground, ground_contact flicker, then tip-over/lift-off and tumble. PID: a small sustained 2.75-3 Hz p/q oscillation (g3_checks item 2 FAIL both keys, line RMS 18/29 deg/s; corrected by owner review S186, was "no oscillation"), no pitch limit cycle, touchdown
77.19 s, ground_contact 77.64, maybe_landed 78.0, landed 78.35, disarm 80.36.

## Mechanism (hypothesis supported by cross-run data, not isolated)
Pitch loop gain too high for the slow plant: draw has pitch controller G1 / plant G1 e=1.52 (G1_P x1.2346, Iyy x1.234), motor tau x2.28 with
tau_down/up 2.41, 19.9 % eRPM frame dropout, eRPM latency 2 frames, 1.25 ms loop delay. Same 20 s window rms of the rate across G3 runs
(`run_0xx`, 45-65 s): oscillating runs 003 (e_p 1.93, tau 2.79), 007 (e_p 1.79, tau 1.36, delay 7.5), 017 (e_p 1.52, tau 2.28),
013 (roll axis, e_r 1.73); stable ones have lower e or lower tau (012: e 1.65/1.78 but tau 0.54). Pattern = overestimated G1 times slow
motors. Not shown: which firmware term sets the margin (INDI_ACT_TC 0.033 vs plant tau, lead gain, K_P=20, measured-torque path).

## Open
- INDI-specific: yes for the oscillation (PID same draw: q RMS <= 0.95 rad/s, a small 2.5-3.25 Hz p/q line that fails item 2 but no limit cycle, ~25x below INDI), but the PID has the same G1 draw only via plant, not G1 gain.
- Why scored window 62-65 s was judged only on tilt: oscillation flag was raised (p, q, r), loss came from touchdown.
- Not checked: indi_pos ground handling during the bounce (76.7 s stage_mode 2) as secondary contributor to the 77.2 s thrust spike.
- Not checked: nominal-plant pitch margin sweep (would need a flight).
- Firmware file for a margin fix, if confirmed: src/lib/indi_rate_control/ (rate loop), src/modules/mc_indi_rate_control/; not edited.
