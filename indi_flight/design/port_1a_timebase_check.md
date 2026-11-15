# Port 1a: time base and origin check for the analytic trajectory metric

Command: `python3 indi_flight/bench/timebase_check.py indi_project/results/s8g_zsine_delay/seed1 indi_project/results/s8l_o13_gnss0/o1_lemniscate/pid_tuned/seed1 indi_project/results/s8l_o13_gnss0/o2_circle_z/pid_tuned/seed1`
(read-only; uses `metrics.py` functions `analytic_reference`, `trajectory_error_analytic`, `offboard_span`, `topic`; scan -100..+100 ms in 2 ms steps; lag L means reference at `t - (t0_us + L)`, positive = reference delayed.)

Scoring window = `t_window_*_us` intersected with the nav_state==14 span. Pre-t0 = [window start, t0] (3 s settle hover, ~150 truth samples).

| run (traj) | truth argmin lag | truth RMS lag0 -> argmin (m) | estimate argmin lag | estimate RMS lag0 -> argmin (m) | setpoint argmin lag | setpoint RMS lag0 -> argmin (m) | origin offset pre-t0 N/E/D (cm) | origin offset window N/E/D (cm) |
|---|---|---|---|---|---|---|---|---|
| s8g_zsine_delay/seed1 (zmulti, vertical) | -4 ms (flat) | 0.0547 -> 0.0547 | -48 ms | 0.0368 -> 0.0337 | +2 ms | 0.0009 -> 0.0004 | +2.6 / -0.5 / -0.0 | +2.9 / -0.2 / -0.4 |
| s8l o1_lemniscate (5 x 2.5 m) | +100 ms (edge) | 0.7178 -> 0.4968 | +100 ms (edge) | 0.6481 -> 0.4137 | +2 ms | 0.0098 -> 0.0043 | +2.4 / +0.2 / -4.9 | +3.3 / +1.0 / -4.5 |
| s8l o2_circle_z (r 5 m, z 0.75 m) | +100 ms (edge) | 0.8188 -> 0.6311 | +100 ms (edge) | 0.7350 -> 0.5300 | +4 ms | 0.0131 -> 0.0055 | +0.1 / -0.8 / +0.5 | +1.8 / -1.0 / -0.3 |

Extended truth scan (-100..+400 ms, diagnostic only, not in the command): lemniscate minimum at +160 ms (0.447 m),
circle minimum at +120 ms (0.631 m). These are the control tracking lag, not a time-base offset.

## Conclusion
- Time correction: NO. The setpoint point comparison (no ZOH, no control lag) gives +2 to +4 ms with RMS at lag 0 of
  at most 1.3 cm. The truth and estimate minima sit at the scan edge or at 120-160 ms, which is tracking lag that a
  t0 correction would wrongly absorb.
- Origin correction: YES by the rule. N offset is +2.4 to +3.3 cm in zmulti and lemniscate, and Z is -4.9 cm in
  lemniscate (pre-t0 and window agree, so it is a stable bias). Circle stays under 2 cm.

## UNVERIFIED
- That `trajectory_setpoint` timestamps are the PX4 receive time, so the +2..+4 ms setpoint lag is transport latency
  (not checked against the runner's send code).
- Whether the N/Z offsets are estimator bias (baro/GNSS) or a true origin mismatch; no GNSS/baro log was checked.
- The ported `compute()` was not run end-to-end; the table uses the same functions it calls. Archive `metrics.json`
  files are the old format (no `truth` block), so they were not compared.
- Only 3 runs (1 vertical, 2 horizontal); the lemniscate and circle truth RMS (0.5-0.8 m) is much larger than the
  zmulti run, and the tracking-lag explanation was not separately verified.
- Setpoint lag resolution: setpoint is 5 Hz, a 1 ms shift changes a 5 m/s trajectory by 5 mm, so argmin is +/-1-2 ms.

## Orchestrator decision (session 8)
Re-ran the command on the first two runs: same table. Time base: accepted, no t0 correction (setpoint check +2..+4 ms,
<= 2 cm at 5 m/s). Origin: NOT corrected, against the agent's rule. The reference is commanded in the estimator frame,
so truth vs reference is the physical tracking error and includes estimator bias by design (lesson 3); the bias is
reported separately in `truth_minus_estimate_pre_t0_ned_m`, which the gate report must show next to the truth RMS.
Overturn if a bias above ~10 % of a gate threshold appears, then split truth error into tracking + estimator parts.
Open: horizontal truth RMS 0.5-0.8 m on PID lemniscate/circle (archive pid_tuned) is large; tracking-lag explanation
unverified (extended scan min at +120..160 ms). Not an anomaly of the metric; revisit when PID is re-flown on the ref airframe.
