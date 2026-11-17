# T119 stage-3 items 3 and 2 (S59)

## Plan
- Item 3 (D-S3-SPTO): pure `RateSetpointWatchdog` (last rx stamp, now, armed, uses_setpoint -> stale, zero_rates, warn).
  Stale = armed && uses && (never received || age > MC_INDI_SP_TO). Module zeroes `_rates_setpoint`, thrust is held
  (it is only overwritten by a message), `rate_sp_stale` in indi_rate_status, warning on rising edge then every 2 s.
  Inactive disarmed and in the acro branch. MC_INDI_SP_TO default 0.5, 0.05..2.
- Item 2: (i) init() refuses to start (PX4_ERR, false) if vehicle_torque_setpoint is advertised with a sample younger than
  0.5 s. (ii) pure `TorqueStampTracker`: ring of 4 own `vehicle_torque_setpoint.timestamp` (set from one
  hrt_absolute_time() that is also what the module records, so the match is exact); received message not in ring =
  foreign -> `foreign_torque_pub` (cleared after 100 consecutive own), PX4_ERR every 2 s. History is consumed in init().
  rc.mc_apps: one INDI-only comment line, stock logic unchanged.

## Files touched
- src/modules/mc_indi_rate_control/{RateSetpointWatchdog,TorqueStampTracker}.{hpp,cpp} (new, lib IndiSafety)
- src/modules/mc_indi_rate_control/{McIndiRateControl.hpp,.cpp,CMakeLists.txt,mc_indi_rate_control_params.yaml}
- msg/IndiRateStatus.msg (+rate_sp_stale, +foreign_torque_pub), ROMFS/px4fmu_common/init.d/rc.mc_apps (comment)

## New tests
- IndiRateSetpointWatchdogTest (6), IndiTorqueStampTrackerTest (4)

## Test results
- `make tests 'TESTFILTER=[iI]ndi'`: 6/6 targets pass (incl. 2 new, 10 new cases). SITL `make px4_sitl_default`: links bin/px4 OK.
- astyle check_code_style.sh on module dir: no output (clean).

## Break-checks
- zero_rates forced false: IndiRateSetpointWatchdog failed; restored.
- foreign match disabled (`if (false)`): IndiTorqueStampTracker failed; restored, 6/6 green.

## UNVERIFIED
- Module-level wiring (init refusal, run-time PX4_ERR, rate_sp_stale in log) compiled but not exercised in SITL.
