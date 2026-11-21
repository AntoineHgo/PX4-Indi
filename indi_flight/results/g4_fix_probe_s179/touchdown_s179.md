# G4 AUTO_LAND chatter flag vs touchdown (S179, log analysis only)

## Conclusion
1. The flag is at TOUCHDOWN, not in steady descent and not on the ground after landed. Flagged detector spans (4 s windows) 66-72 s only look wide; the motor line RMS crosses 5e-4 only in 1 s windows that contain the ground impact (about gc-0.5 s to landed+0.7 s). Examples baseline: diffB 5-6e-4 for 68.0-69.5 s, collective 1e-3 (a thrust step, ratio only ~x11, not a line).
2. Descent (last 2 s before ground_contact) holds a real 20-22 Hz line (diffB/C ratio x500 in torque_setpoint, rates_sp roll) but at 1.3e-4 (baseline) or 6e-5 (F3) on motor diffB/C, below 5e-4. Post-landed (landed to disarm): line RMS ~1e-5 (motors constant/zero, gyro 2e-4 floor), no flag possible.
3. Land detector lag: ground_contact is 0.2-0.25 s after the true ground (gt alt ~0), maybe_landed +0.34 s, landed +0.67 s. blend_hold and stage_mode 2 rise together with ground_contact (stage_mode=2 from gc on); blend_frozen toggles 0.3-0.5 s before gc (impact).
4. PID reference shows the same effect at touchdown: a 26 Hz detector line (65.5-71 s, 1.2e-3, not sustained) and, at 20 Hz, diffB 5e-4 / torque_setpoint 8e-4 / gyro 1e-2 in the impact window 67.5-68.5 s, then ~1e-5 on the ground. So the INDI flag is largely an impact-transient artefact plus a modest descent line; the INDI-specific part is the descent line (torque_setpoint x500 vs PID x5, rates_sp roll 4e-3 vs PID 2e-3) and its extension to 68-69.5 at 6e-4 (PID is 1e-4 in 68-69).
5. Caveat: 0.5 s Welch segments (2 Hz bins, 1.0 s windows) cannot separate a line from an impact transient; the broadband impact has ratio < 20 in collective and gyro. Separating them needs the detector's own 4 s windows shifted to end at ground_contact (not done).

## Method
Timeline: pyulog snippet (vehicle_status, vehicle_land_detected, vehicle_local_position[_groundtruth], indi_pos_status). Detector flagged spans: chatter_cruise_s176.py run in docker (needs scipy; key1 fixed +-2 Hz, window 4 s, t0-t1 = window start-end). Line RMS: chatter_chain_s178.analyse with WINDOWS overridden to descent (gc-2..gc), touchdown, post-landed plus sliding 1.0 s windows step 0.5 s; Welch segment 0.5 s (the script needs window >= 1.5 x segment, so 2 s Welch fails for touchdown = 0.67 s; touchdown window padded to gc-0.2..landed+0.15 = ~1.0 s). Band 19-23 Hz (PID also 24-28), RMS +-1 Hz around the peak, units native (motor control units, rad/s, N*m normalised as logged). Best component per signal chosen by max ratio over all windows. Table cell = peak Hz, ratio peak/median(20-0.9 Nyq), line RMS.

Commands:
```
docker: indi_project/docker/run.sh -n tdrs -t 450 -- python3 indi_flight/results/g4_gate_s169/chatter_cruise_s176.py <5 run dirs>
host:   python3 <scratch>/td.py <run dir> [pid]   # imports indi_flight/bench/chatter_chain_s178.py, overrides WINDOWS (scratch script: /tmp/claude-1001/.../scratchpad/td.py, td2.py)
```

## Timelines (log time s)
| log | AUTO_LAND (18) | true ground (gt alt <0.1 / ~0) | ground_contact | maybe_landed | landed | disarm / nav 18->14 | stage_mode=2, blend_hold | blend_frozen | detector flagged span (peak Hz, max RMS) |
|---|---|---|---|---|---|---|---|---|---|
| INDI baseline cruise_typ_s1 (freeze7) | 60.33 | 67.63 / ~67.95 | 68.14 | 68.47 | 68.81 | 70.82 | 68.15 | 67.8, 67.86 | 66.0-72.0 (20.3, 2.2e-3) |
| F3 s1 flagged | 61.64 | 69.05 / ~69.3 | 69.55 | 69.89 | 70.24 | 72.25 | 69.56 | 69.28, 69.56 | 66.0-72.0 (20.3, 1.8e-3) |
| F3 s3 flagged | 61.29 | 69.15 / ~69.4 | 69.67 | 70.01 | 70.34 | 72.35 | 69.68 | 69.38-69.5, 69.68 | 66.0-73.0 (20.3, 3.1e-3) |
| F3 s2 not flagged | 61.08 | 68.76 / ~69.0 | 69.28 | 69.62 | 69.95 | 71.96 | 69.29 | 68.99-69.1, 69.29 | none in land phase |
| PID cruise_typ_s1 | 60.54 | 67.92 / ~68.2 | 68.44 | 68.80 | 69.14 | 71.14 | n/a | n/a | 65.5-71.0 (26.0, 1.2e-3) |

(INDI descent ~0.7 m/s from AUTO_LAND +~1 s; flagged-window counts in land-cmd phase: baseline 5/32, F3 s1 5/30, s3 7/33, s2 0/32, PID 4/30.)

## INDI baseline cruise_typ_s1  (band 19-23 Hz)

gc 68.14 landed 68.81 disarm 70.82 band (19, 23)
| signal | descent | touchdown | post-landed |
| rates_sp roll | 22Hz x7 3.8e-03 | 20Hz x84 1.6e-03 | 20Hz x12 1.3e-05 |
| gyro xyz[1] | 20Hz x70 5.7e-04 | 22Hz x13 2.2e-04 | 20Hz x6 1.6e-04 |
| torque_setpoint xyz[1] | 22Hz x6 2.6e-04 | 20Hz x35 4.5e-04 | 20Hz x3 9.6e-06 |
| thrust_setpoint xyz[2] | 20Hz x9 6.5e-04 | 20Hz x9 3.1e-04 | 20Hz x1 6.3e-07 |
| actuator_motors collective  | 20Hz x9 6.5e-04 | 20Hz x9 3.1e-04 | 20Hz x1 6.3e-07 |
| actuator_motors diffB  | 20Hz x14 2.5e-04 | 20Hz x71 3.0e-04 | 20Hz x3 6.8e-06 |
| actuator_motors diffC  | 20Hz x4 1.4e-04 | 22Hz x2 5.9e-06 | 20Hz x3 7.9e-06 |


Sliding (rms only)
```
sliding 1.0 s windows (start) line RMS: 65.0 65.5 66.0 66.5 67.0 67.5 68.0 68.5 69.0 69.5 70.0 70.5 71.0 71.5 72.0
rates_sp roll                            4e-03 4e-03 4e-03 4e-03 6e-03 6e-03 7e-04 9e-06 1e-05 1e-05 1e-05 9e-06 9e-06 8e-06 9e-06
gyro xyz[1]                              7e-04 8e-04 7e-04 6e-04 6e-04 2e-04 2e-04 1e-04 2e-04 1e-04 2e-04 2e-04 2e-04 2e-04 2e-04
torque_setpoint xyz[1]                   2e-04 2e-04 2e-04 2e-04 2e-04 4e-04 8e-04 8e-04 1e-05 9e-06 1e-05 1e-05 1e-05 1e-05 1e-05
thrust_setpoint xyz[2]                   2e-05 2e-05 2e-05 2e-05 1e-03 1e-03 6e-04 6e-04 0e+00 0e+00 5e-06 5e-06 0e+00 0e+00 0e+00
actuator_motors collective               2e-05 2e-05 2e-05 2e-05 1e-03 1e-03 6e-04 6e-04 0e+00 0e+00 5e-06 5e-06 6e-13 6e-13 6e-13
actuator_motors diffB                    1e-04 1e-04 1e-04 1e-04 2e-04 3e-04 5e-04 6e-04 8e-06 7e-06 8e-06 8e-06 9e-06 7e-06 1e-05
actuator_motors diffC                    1e-04 1e-04 1e-04 1e-04 1e-04 1e-04 5e-06 6e-06 9e-06 8e-06 8e-06 6e-06 5e-06 5e-06 6e-06
```

## F3 s1 (flagged)  (band 19-23 Hz)

gc 69.55 landed 70.24 disarm 72.25 band (19, 23)
| signal | descent | touchdown | post-landed |
| rates_sp roll | 20Hz x28 5.1e-03 | 20Hz x1 7.3e-04 | 20Hz x10 1.1e-05 |
| gyro xyz[0] | 20Hz x6 8.1e-03 | 22Hz x1 1.0e-04 | 20Hz x6 1.7e-04 |
| torque_setpoint xyz[2] | 20Hz x364 3.4e-05 | 20Hz x13 3.3e-05 | 22Hz x5 8.0e-07 |
| thrust_setpoint xyz[2] | 20Hz x12 5.2e-04 | 20Hz x9 2.7e-04 | 20Hz x2 7.7e-07 |
| actuator_motors collective  | 20Hz x15 5.4e-04 | 20Hz x9 2.7e-04 | 20Hz x2 7.7e-07 |
| actuator_motors diffB  | 22Hz x4 6.1e-04 | 20Hz x4 9.3e-05 | 22Hz x7 8.9e-06 |
| actuator_motors diffC  | 22Hz x3 4.4e-04 | 20Hz x2 6.3e-05 | 20Hz x3 6.8e-06 |


Sliding (rms only)
```
sliding 1.0 s windows (start) line RMS: 66.0 66.5 67.0 67.5 68.0 68.5 69.0 69.5 70.0 70.5 71.0 71.5 72.0 72.5 73.0 73.5
rates_sp roll                            2e-03 2e-03 2e-03 2e-03 2e-03 7e-03 7e-03 2e-04 9e-06 1e-05 1e-05 1e-05 1e-05 9e-06 7e-06 8e-06
gyro xyz[0]                              4e-04 4e-04 6e-04 5e-04 4e-04 2e-02 2e-02 1e-04 2e-04 2e-04 2e-04 2e-04 2e-04 2e-04 1e-04 1e-04
torque_setpoint xyz[2]                   1e-05 1e-05 1e-05 6e-06 1e-05 5e-05 5e-05 7e-05 7e-05 6e-07 9e-07 9e-07 9e-07 7e-07 7e-07 8e-07
thrust_setpoint xyz[2]                   2e-05 2e-05 2e-05 2e-05 2e-05 1e-03 1e-03 7e-04 7e-04 0e+00 0e+00 6e-06 6e-06 0e+00 0e+00 0e+00
actuator_motors collective               2e-05 2e-05 2e-05 1e-05 2e-05 1e-03 1e-03 7e-04 7e-04 0e+00 0e+00 6e-06 6e-06 8e-13 6e-13 4e-13
actuator_motors diffB                    6e-05 6e-05 7e-05 7e-05 7e-05 1e-03 1e-03 2e-04 2e-04 1e-05 7e-06 7e-06 7e-06 6e-06 7e-06 4e-06
actuator_motors diffC                    6e-05 7e-05 9e-05 8e-05 7e-05 8e-04 8e-04 8e-05 8e-05 7e-06 8e-06 8e-06 8e-06 7e-06 5e-06 5e-06
```

## F3 s3 (flagged)  (band 19-23 Hz)

gc 69.67 landed 70.34 disarm 72.35 band (19, 23)
| signal | descent | touchdown | post-landed |
| rates_sp pitch | 20Hz x21 1.2e-02 | 20Hz x5 1.6e-03 | 22Hz x11 1.2e-05 |
| gyro xyz[1] | 20Hz x20 9.2e-03 | 22Hz x11 2.3e-04 | 22Hz x9 2.0e-04 |
| torque_setpoint xyz[2] | 20Hz x255 3.9e-05 | 20Hz x9 9.9e-05 | 20Hz x3 5.8e-07 |
| thrust_setpoint xyz[2] | 20Hz x13 5.0e-04 | 20Hz x9 3.2e-04 | 20Hz x1 6.3e-07 |
| actuator_motors collective  | 20Hz x13 5.0e-04 | 20Hz x9 3.2e-04 | 20Hz x1 6.3e-07 |
| actuator_motors diffB  | 20Hz x10 7.6e-04 | 20Hz x8 1.8e-04 | 22Hz x6 9.1e-06 |
| actuator_motors diffC  | 20Hz x15 3.3e-04 | 20Hz x3 5.4e-05 | 20Hz x4 7.3e-06 |


Sliding (rms only)
```
sliding 1.0 s windows (start) line RMS: 66.0 66.5 67.0 67.5 68.0 68.5 69.0 69.5 70.0 70.5 71.0 71.5 72.0 72.5 73.0 73.5
rates_sp pitch                           2e-03 2e-03 2e-03 2e-03 2e-03 6e-03 2e-02 9e-04 2e-05 1e-05 9e-06 1e-05 8e-06 1e-05 1e-05 1e-05
gyro xyz[1]                              2e-04 4e-04 3e-04 3e-04 4e-04 2e-02 2e-02 2e-04 3e-04 2e-04 1e-04 2e-04 1e-04 2e-04 2e-04 2e-04
torque_setpoint xyz[2]                   1e-05 1e-05 1e-05 1e-05 1e-05 2e-05 5e-05 1e-04 2e-04 5e-07 8e-07 8e-07 8e-07 5e-07 6e-07 7e-07
thrust_setpoint xyz[2]                   2e-05 2e-05 2e-05 2e-05 2e-05 9e-04 9e-04 5e-04 5e-04 0e+00 0e+00 4e-06 5e-06 0e+00 0e+00 0e+00
actuator_motors collective               2e-05 2e-05 2e-05 2e-05 2e-05 9e-04 9e-04 5e-04 5e-04 3e-13 3e-13 4e-06 5e-06 7e-13 1e-12 1e-12
actuator_motors diffB                    6e-05 6e-05 7e-05 6e-05 7e-05 1e-03 1e-03 2e-04 2e-04 9e-06 6e-06 8e-06 6e-06 9e-06 8e-06 1e-05
actuator_motors diffC                    6e-05 7e-05 7e-05 7e-05 6e-05 2e-04 4e-04 7e-05 8e-05 7e-06 8e-06 8e-06 7e-06 7e-06 6e-06 7e-06
```

## F3 s2 (not flagged)  (band 19-23 Hz)

gc 69.28 landed 69.95 disarm 71.96 band (19, 23)
| signal | descent | touchdown | post-landed |
| rates_sp pitch | 20Hz x13 2.0e-03 | 20Hz x2 4.6e-04 | 22Hz x10 1.1e-05 |
| gyro xyz[1] | 20Hz x6 3.5e-03 | 22Hz x12 2.3e-04 | 22Hz x7 1.8e-04 |
| torque_setpoint xyz[1] | 22Hz x4 3.5e-04 | 22Hz x3 1.2e-04 | 22Hz x5 1.1e-05 |
| thrust_setpoint xyz[2] | 20Hz x11 5.3e-04 | 20Hz x9 3.2e-04 | 20Hz x2 9.1e-07 |
| actuator_motors collective  | 20Hz x11 5.3e-04 | 20Hz x9 3.1e-04 | 20Hz x2 1.1e-06 |
| actuator_motors diffB  | 22Hz x3 2.5e-04 | 22Hz x3 8.6e-05 | 22Hz x4 8.0e-06 |
| actuator_motors diffC  | 20Hz x1 2.2e-04 | 20Hz x2 6.7e-05 | 22Hz x3 7.1e-06 |


Sliding (rms only)
```
sliding 1.0 s windows (start) line RMS: 66.0 66.5 67.0 67.5 68.0 68.5 69.0 69.5 70.0 70.5 71.0 71.5 72.0 72.5 73.0
rates_sp pitch                           2e-03 2e-03 2e-03 2e-03 2e-03 2e-03 1e-03 1e-05 1e-05 9e-06 8e-06 1e-05 8e-06 1e-05 8e-06
gyro xyz[1]                              4e-04 5e-04 4e-04 3e-04 2e-03 6e-03 3e-04 2e-04 2e-04 1e-04 1e-04 2e-04 1e-04 2e-04 1e-04
torque_setpoint xyz[1]                   9e-05 1e-04 1e-04 9e-05 1e-04 6e-04 7e-05 2e-04 1e-05 9e-06 9e-06 1e-05 8e-06 1e-05 8e-06
thrust_setpoint xyz[2]                   2e-05 2e-05 2e-05 2e-05 3e-04 9e-04 3e-05 7e-04 0e+00 0e+00 2e-07 6e-06 0e+00 0e+00 0e+00
actuator_motors collective               2e-05 2e-05 2e-05 2e-05 3e-04 9e-04 3e-05 7e-04 2e-13 2e-13 2e-07 6e-06 9e-13 9e-13 5e-13
actuator_motors diffB                    6e-05 8e-05 7e-05 6e-05 1e-04 4e-04 5e-05 2e-04 1e-05 7e-06 6e-06 7e-06 5e-06 8e-06 6e-06
actuator_motors diffC                    5e-05 7e-05 7e-05 6e-05 1e-04 3e-04 9e-05 9e-05 1e-05 8e-06 7e-06 7e-06 9e-06 9e-06 7e-06
```

## PID cruise_typ_s1 band 19-23 Hz

gc 68.44 landed 69.14 disarm 71.14 band (19, 23)
| signal | descent | touchdown | post-landed |
| rates_sp pitch | 20Hz x73 1.8e-03 | 20Hz x3 9.7e-05 | 22Hz x7 9.0e-06 |
| gyro xyz[1] | 22Hz x7 5.2e-03 | 22Hz x11 2.2e-04 | 22Hz x5 1.6e-04 |
| torque_setpoint xyz[1] | 22Hz x5 4.1e-04 | 22Hz x8 1.8e-05 | 22Hz x3 1.2e-05 |
| thrust_setpoint xyz[2] | 20Hz x8 2.9e-04 | 20Hz x8 4.2e-04 | 20Hz x1 6.4e-07 |
| actuator_motors collective  | 20Hz x8 2.9e-04 | 20Hz x8 4.2e-04 | 20Hz x1 6.4e-07 |
| actuator_motors diffB  | 22Hz x5 2.9e-04 | 22Hz x10 1.4e-05 | 20Hz x1 4.4e-09 |
| actuator_motors diffC  | 20Hz x66 5.5e-05 | 22Hz x2 7.8e-06 | 20Hz x1 1.4e-09 |


Sliding (rms only)
```
sliding 1.0 s windows (start) line RMS: 65.0 65.5 66.0 66.5 67.0 67.5 68.0 68.5 69.0 69.5 70.0 70.5 71.0 71.5 72.0 72.5
rates_sp pitch                           2e-03 2e-03 2e-03 2e-03 2e-03 1e-03 2e-04 1e-05 1e-05 7e-06 1e-05 1e-05 1e-05 9e-06 9e-06 1e-05
gyro xyz[1]                              3e-04 4e-04 2e-04 4e-04 4e-04 1e-02 2e-03 3e-04 2e-04 1e-04 2e-04 2e-04 2e-04 2e-04 1e-04 2e-04
torque_setpoint xyz[1]                   8e-05 9e-05 8e-05 9e-05 8e-05 8e-04 2e-04 2e-05 2e-05 1e-05 1e-05 2e-05 2e-05 1e-05 1e-05 1e-05
thrust_setpoint xyz[2]                   2e-05 2e-05 2e-05 2e-05 2e-05 5e-04 4e-04 5e-04 5e-04 0e+00 0e+00 0e+00 0e+00 0e+00 0e+00 0e+00
actuator_motors collective               2e-05 2e-05 2e-05 2e-05 2e-05 5e-04 4e-04 5e-04 5e-04 1e-12 2e-12 1e-12 7e-13 4e-13 6e-13 6e-13
actuator_motors diffB                    6e-05 6e-05 5e-05 6e-05 6e-05 5e-04 1e-04 1e-05 5e-06 1e-12 2e-12 1e-05 1e-05 9e-06 7e-06 9e-06
actuator_motors diffC                    5e-05 5e-05 6e-05 5e-05 6e-05 5e-05 1e-05 7e-06 2e-06 3e-12 4e-12 6e-06 1e-05 8e-06 9e-06 5e-06
```

## PID cruise_typ_s1 band 24-28 Hz (detector peak 26 Hz)

gc 68.44 landed 69.14 disarm 71.14 band (24, 28)
| signal | descent | touchdown | post-landed |
| rates_sp pitch | 24Hz x3 3.8e-04 | 24Hz x1 6.0e-05 | 24Hz x6 8.4e-06 |
| gyro xyz[1] | 26Hz x14 7.6e-03 | 24Hz x5 1.5e-04 | 24Hz x4 1.5e-04 |
| torque_setpoint xyz[2] | 26Hz x17 9.4e-07 | 24Hz x74 2.3e-06 | 26Hz x61 1.3e-06 |
| thrust_setpoint xyz[2] | 24Hz x5 2.4e-04 | 24Hz x6 3.5e-04 | 24Hz x1 6.3e-07 |
| actuator_motors collective  | 24Hz x5 2.4e-04 | 24Hz x6 3.4e-04 | 24Hz x1 6.3e-07 |
| actuator_motors diffB  | 26Hz x11 4.4e-04 | 24Hz x4 8.2e-06 | 24Hz x1 4.4e-09 |
| actuator_motors diffC  | 26Hz x4 1.4e-05 | 24Hz x5 1.2e-05 | 24Hz x1 1.4e-09 |


Sliding (rms only)
```
sliding 1.0 s windows (start) line RMS: 65.0 65.5 66.0 66.5 67.0 67.5 68.0 68.5 69.0 69.5 70.0 70.5 71.0 71.5 72.0 72.5
rates_sp pitch                           6e-05 2e-04 2e-04 6e-05 1e-04 6e-04 2e-04 1e-05 8e-06 9e-06 1e-05 9e-06 8e-06 8e-06 8e-06 9e-06
gyro xyz[1]                              2e-04 2e-04 2e-04 1e-04 2e-04 1e-02 5e-03 2e-04 1e-04 2e-04 2e-04 2e-04 2e-04 2e-04 2e-04 2e-04
torque_setpoint xyz[2]                   1e-06 1e-06 1e-06 1e-06 9e-07 9e-07 2e-06 2e-06 2e-06 1e-06 1e-06 1e-06 1e-06 1e-06 2e-06 2e-06
thrust_setpoint xyz[2]                   2e-05 1e-05 2e-05 2e-05 2e-05 4e-04 3e-04 4e-04 4e-04 0e+00 0e+00 0e+00 0e+00 0e+00 0e+00 0e+00
actuator_motors collective               2e-05 1e-05 2e-05 2e-05 2e-05 4e-04 3e-04 4e-04 4e-04 2e-12 2e-12 1e-12 6e-13 4e-13 8e-13 7e-13
actuator_motors diffB                    1e-05 1e-05 1e-05 8e-06 1e-05 7e-04 3e-04 9e-06 3e-06 2e-12 2e-12 1e-05 1e-05 9e-06 1e-05 9e-06
actuator_motors diffC                    7e-06 1e-05 1e-05 1e-05 8e-06 2e-05 1e-05 1e-05 7e-07 3e-12 4e-12 6e-06 1e-05 9e-06 1e-05 9e-06
```
