# G5 events injector pre-test (S142, agent A142, read S143)

Script `bench/g5_events.py` (self-test `bench/tests/test_g5_events.py`, 5 tests OK, unkeyed). One AUTO-hold flight
at 3 m, quad5in, matched GNSS 110 ms, events in sequence: EKF yaw 5 deg, EKF xy 1 m, RC loss, link loss, offboard
loss, kill -> re-arm -> take-off -> land. Raw logs ignored (`*.ulg`, `*.log`, `sends.csv`).

| flight | result |
|---|---|
| flight1_rcfail | set-up fault: kill never applied (motors never 0), applied-commanded 3-24 ms |
| flight2 | kill PASS (motors 0 87.5 ms after flag), offboard-loss PASS timing; ekf_yaw effect not visible (0.0006 of 5 deg: injection not taken by EKF); rc_loss effect not visible; applied-commanded 3 ms on the others |

Findings (details NOTES.md):
- G1.5 "applied within 1 physics step" (1.25 ms) is not met by any MAVLink-side event: runner ticks are 10-20 ms
  in lockstep, applied-commanded 3-24 ms. Applied time IS logged (flags/counters). Owner question Q8.
- G5.6 maybe_landed and G5.11 z reset are not injectable without firmware (land detector needs ground contact;
  external position reset is horizontal only). Q8.
- ekf_yaw injector defect (no effect); rc_loss effect not detected by the check. To fix before the rows fly.
- Failsafe onset: link loss flag 5.3 s after last message (timeout 3 s), offboard loss 4.0 s (timeout 1 s): onset
  lateness above G5.8 "<= 1 s after its timeout" in a probe; check the flag source/log rate (failsafe_flags 2 Hz)
  before reading it as a failure.
