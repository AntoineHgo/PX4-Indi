# S122 INDI re-fly of T118 idx 0/21/49 with the measured-torque path on

Same draws as g3_refly_s121 (seed 117, n 60), base params now with MC_INDI_W_MAX 2700 (0a49572149). Rate loop INDI,
outer loop stock mc_pos_control. Probe, not gate evidence. Command: `setsid nohup bash indi_flight/results/g3_refly_s122/fly.sh 3 0 21 49`.
Validity (run_validity.py, unkeyed) in each g3_done.json: all three valid (params match the log, indi_rate_status 800 Hz).

| idx | mode after take-off | outcome | measured_torque_in_use mean (whole log, 0 before arming) | z min/mean/max m, t 40 s to end-15 s |
|---|---|---|---|---|
| 0 | ACRO 37 s, LAND 69 s | ok | 0.79 | 3.83 / 5.71 / 8.43 |
| 21 | STABILIZED 37 s, LAND 68 s | ok | 0.79 | 3.19 / 5.29 / 7.49 |
| 49 | STABILIZED 37 s, LAND 69 s | ok | 0.80 | 2.78 / 4.80 / 7.04 |

Altitude swings are the open-loop z-sine collective of the stick pilot (manual modes), as in T118 for PID.
actuator_torque_measured is now logged. Model-only runs of the same draws: g3_refly_s121 (idx 0 ok, 49 aborted:
after LAND the runner's pilot sticks switched to POSCTL (nav 2) and it hovered until the wall timeout, known K118 runner MINOR).
