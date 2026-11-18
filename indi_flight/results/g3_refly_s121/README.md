# S121 INDI re-fly of T118 (idx 0/21/49)

Why: every "indi" G3 run S110-S118 flew the stock rate loop (base params lacked MC_RATE_CTL_TYPE 1). This re-flies
the T118 stick-pilot draws (seed 117, n 60) with the INDI rate loop actually running. Outer loop is stock
mc_pos_control (MC_INDI_POS_EN unset). Probe, not gate evidence. PID controls: `results/g3_pilot_s118/pid_run0NN`.

Command: `setsid nohup bash indi_flight/results/g3_refly_s121/fly.sh 2 0 49` (idx 21 was flown alone first).
Raw ulog/console untracked (gitignore).

| idx | mode | INDI really on | result |
|---|---|---|---|
| 21 | POSCTL take-off, STABILIZED from 37.9 s, LAND 69.8 s | boot MC_INDI_EN=1, indi_rate_status 800 Hz | ok: z held 4.95-5.84 m mean under the z-sine sticks, landed and disarmed 80.4 s |

Signal check (run_021): esc_status logged at 750 Hz (not 100 Hz as the H120 note claimed); actuator_torque_measured
not in the log (topic name only in the format section).
| 0 | ACRO 38 s, LAND 69 s, then POSCTL 70 s | boot MC_INDI_EN=1 | ok; z 3.80/5.68/8.45 |
| 49 | STABILIZED 38 s, LAND 70 s, then POSCTL 71 s | boot MC_INDI_EN=1 | aborted: wall timeout in 'land' (pilot sticks after LAND -> POSCTL, K118 MINOR) |

S122: all runs here flew with MC_INDI_W_MAX unset, so on the actuator MODEL only (measured_torque_in_use 0).
Measured-path re-fly: ../g3_refly_s122.
