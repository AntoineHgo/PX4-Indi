# Stage-8 review finding 2: a_f / t_f lag, preliminary identification (session 52, 2026-11-15)

Script: `bench/ident_s8_delay.py <flight.ulg> <MC_INDIP_DLY>` (cross-correlation of the detrended indi_pos_status
a_f and t_f, z component; x/y follow the attitude in both signals and correlate at every lag, uninformative).
Hover seed 1, v2 sim with vibration, after the window-average fix, MC_INDIP_DLY = 1 (8 ms cycles):

| log | peak lag (logged t_f vs a_f) | raw eRPM vs a_f | corr at lag -4..+1 |
|---|---|---|---|
| s8c_accel_window | -3 | eRPM leads by 4 cycles | 0.90 0.94 0.93 0.88 0.79 0.67 |
| s8d_fix45 | -2 | (flat: a 0.33 m vertical transient dominates) | 0.99 at all lags |
| s8e_qd_metric | -3 | eRPM leads by 4 cycles | 0.90 0.92 0.92 0.90 0.86 0.80 |

Reading: in this simulation the eRPM thrust LEADS the measured specific force by ~3-4 control cycles (24-32 ms).
Delaying u (what MC_INDIP_DLY does) is therefore the right direction, contrary to the reason written in the spec
("eRPM arrives later"); the value 1 is too small. The peak is broad (hover, little vertical excitation), and a
~30 ms accelerometer lag is not explained yet (the physics gives thrust -> acceleration instantly; candidates:
gz IMU / bridge pipeline, the v2 eRPM source). Not applied: confirm on a log with vertical excitation (z step or
trajectory), find the cause of the lag, then set MC_INDIP_DLY from it (identification, not tuning, O-5).

Follow-up, T7 payload_add (`bench/s8f_delay_payload.sh`, `results/s8f_delay_payload/seed1/delay.txt`): z peak at
-5 cycles with correlation 0.11 at every lag: INCONCLUSIVE. A mass step is the wrong excitation: u rises to carry
the payload while a_f returns to zero, so the two signals decorrelate by construction (t_f and a_f differ by the
unmodelled force). The identification needs a commanded vertical acceleration with the plant as modelled: add a
diagnostic z-step (or vertical sine) scenario to `bench/scenarios.py` (diagnostic, outside T/H/V sets) and use it.
