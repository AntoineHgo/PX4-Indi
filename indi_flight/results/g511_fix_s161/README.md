# S161 G5.11 yaw-reset fix (D-T10-RESET) and re-fly

Cause (../g5_freeze_s157/g511_yaw_cause.md): the estimator-reset branch re-seeded the INDI stage's measured-force
filter with one raw accelerometer sample -> a_f step 0.33 m/s^2 -> 1.9 deg tilt-command spike at the 5 deg yaw reset.
Fix: 49568bcaa5 (jerk history only) + d1b65d0f09 (key2 MAJORs, design/review_s161_t10.md: separate jerk-only flag so
position entry / Hold->run / stage reset keep the full restart; test that the jerk history is cleared). Both new unit
tests break-checked.

probe_v1_s1 (firmware 49568bcaa5, superseded, NOT evidence): ekf_yaw tilt jump 1.08 deg (was 1.94), ekf_xy 6.10 deg.
Noise floor, same metric at no-event instants t_a-2..-9 s (host script in S161 session, UNKEYED):
- INDI probe_v1_s1: 0.91 0.72 1.06 0.76 0.87 1.10 0.80 0.75 deg (event 1.08 is inside this range)
- PID g5_events_s1_pid (freeze): 0.48 0.48 0.54 0.49 0.70 0.86 0.64 0.63 deg
=> after the fix no reset-specific spike is left on s1; the residual is INDI hover tilt-command noise under the
typical profile (max over a 1 s window ~0.7-1.1 deg vs PID 0.5-0.9). The 1 deg limit sits at INDI's noise floor:
reported as a G4-type finding (Q12 addendum), the row is scored as written.

Re-fly at d1b65d0f09 (freeze plant/params, typical noise), g511_check.txt (UNKEYED):
| seed | ekf_yaw tilt jump deg (<=1) | yaw no-event min/max deg | ekf_xy tilt jump deg | excursion m (<=0.5) | osc |
| s1 | 0.76 PASS | 0.52/0.78 | 5.81 FAIL (Q12) | 0.05 / 0.21 | none |
| s2 | 1.21 FAIL | 0.74/1.03 | 6.24 FAIL (Q12) | 0.06 / 0.16 | none |
| s3 | 0.83 PASS | 0.73/1.20 | 6.74 FAIL (Q12) | 0.10 / 0.20 | none |
Freeze (before fix): yaw 1.94/1.78/1.84 FAIL 3/3. After: yaw 2/3 PASS as written; s2 is 0.18 deg above its 8
no-event windows (small sample: residual or noise, not resolved). Row G5.11 stays FAIL as written (xy 3/3 Q12,
yaw s2). No sustained oscillation, excursions <= 0.21 m. Unverified: key2 of these scores; no-event floor from 8
windows only.

## S162 keys and re-score (same flights, firmware d1b65d0f09)
G5.11 KEYED: key2_g511.py/.txt (sonnet, written from the GATES 5b text without access to g511_check.py, synthetic
tilt self-test) reproduces every value above: yaw 0.764/1.209/0.827 deg, xy 5.808/6.244/6.736 deg, excursion
0.051-0.209 m, nav_state 4 and one counter increment in every window, yaw no-event range s1 0.52-0.78, s2 0.74-1.03,
s3 0.73-1.20 deg. Oscillation detector not re-keyed (first key only, osc_detector.py self-test). Row G5.11: FAIL as
written (xy 3/3, Q12; yaw s2 1.21 vs its own floor max 1.03), KEYED.
G5.8/G5.9 re-scored at the new firmware (g5_rows_check.py -> g5_events_sN/g5_rows.txt, g5_rows_key2.py ->
g5_rows_key2.txt, values agree): G5.8 hover rc/link/offboard PASS 3/3 (entry - timeout <= 26 ms); G5.9a FAIL s1/s3
as written (switch -> actuator_armed.kill 8.75/1.25/6.25 ms, stock commander latency, Q8 add. 2; outputs 0 at the
kill flag in 0.00 ms, PASS under option A); G5.9b/c/d PASS 3/3 (take-off edge thrust step 4.5-4.6 % of hover). Same
verdicts as the freeze set: the D-T10-RESET change did not move G5.8/G5.9. G5.6 false maybe_landed: not tested (Q8 b).
