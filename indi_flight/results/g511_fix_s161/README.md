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

Re-fly at d1b65d0f09: g5_events_s1..s3 (fly.sh, status.txt); scores below when done.
