# D-omega2 first run-time check (session 35)

Binary: `build/px4_sitl_omega2` (D-omega2 wiring 62c0eb5937 + logger 07c6a39811), flown with `PX4_INDI_BUILD`
while the PID r1f batch used the default build. Params `s2_omega2_check/indi_omega2.params`: frozen v1 INDI
(r4f/c00) + `v2_fac.params` (THR_MDL_FAC 0.683, gyro DNF) + CA_R_W_MAX 1000. Sim v2 (AM32 eRPM model, 1000 Hz IMU,
vibration 1.0/0.05, 1 % eRPM drops). Seed 1, hover at speed 1, step_roll at speed 4. Script `s2_omega2_check/run.sh`.
Single seed, smoke check only, not a benchmark result.

## (a) Measured torque path works

- `indi_rate_status.measured_torque_in_use` = 1 for 97.7 % of the first step_roll log; the model fallback occurs only
  on the ground around arming (37 ms and 158 ms) and at disarm. 0 fault cycles.
- `actuator_torque_measured.valid` 100 % of armed time on both re-flown logs, despite 1 % eRPM frame drops (held
  samples, 20 ms age-out).
- Flight: step_roll roll-rate RMS 0.168/0.169 rad/s (two flights), rise 0.23 s, overshoot 0.4-0.7 %; hover attitude
  RMS 0.12 deg, motor-rate effort 0.038.

Measured vs model torque (`bench/omega2_torque_check.py`, model = vehicle_torque_setpoint through the
MC_INDI_ACT_TC 11.42 ms first-order lag; delay from increments over 40 ms; armed samples):

| log | axis | delay of meas. behind model | incr. corr. | gain meas/model | rms(meas-model) / rms(model) |
|---|---|---|---|---|---|
| step_roll_log | roll | +7 ms | 0.992 | 0.959 | 0.0023 / 0.0250 |
| step_roll_log | pitch | +5 ms | 0.816 | 0.965 | 0.0007 / 0.0040 |
| step_roll_log | yaw | +9 ms | 0.926 | 0.978 | 0.0005 / 0.0027 |
| hover_log | roll | +5 ms | 0.973 | 0.962 | 0.0010 / 0.0121 |
| hover_log | pitch | +4 ms | 0.845 | 0.911 | 0.0005 / 0.0016 |
| hover_log | yaw | +8 ms | 0.931 | 0.939 | 0.0005 / 0.0036 |

Gain within 2-9 % of 1: the omega^2 thrust map with CA_R_W_MAX 1000 and THR_MDL_FAC 0.683 is consistent with the
allocator's model. The measurement lags the 11.42 ms model by 4-9 ms, as expected from the slower identified gz
motor (12.4/25.0 ms up/down, s31) plus the eRPM telemetry latency.

## (b) ERPM delay

`bench/check_sync.py` (span 13 samples = 40 ms; indi_rate_status is logged at 3 ms, so 1 lag sample = 3 ms):
roll (the excited axis) a_f vs measured t_f best lag -1 / 0 / 0 samples on the three step_roll logs (R^2 0.95, 0.95,
0.87). With MC_INDI_ERPM_DLY 1 the measured torque is in step with a_f to within one log sample; the model torque it
replaced would be 5-9 ms early. **MC_INDI_ERPM_DLY stays 1** (finer resolution would need indi_rate_status logged at
1 kHz; not needed at this residual). Pitch/yaw are not excited enough (R^2 < 0.45) to say more.

## Consequence for the v2 controller

In u = omega^2 units the roll effectiveness is G1_R ~ 170-182 (R^2 0.87-0.96), not the frozen 241 (v1 units, FAC
0). Frozen gains therefore run at ~0.72x their designed loop gain on v2: G1 must be re-identified (and the v2 INDI
tuned) before any v2 comparison. Hover logs do not excite the axes enough for G1.
