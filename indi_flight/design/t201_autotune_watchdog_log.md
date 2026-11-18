# T201 log: autotune start (S95 F1) and rate-setpoint watchdog stamp

## A. Autotune (MAJOR) - done per stage3_items_note.md sec. 5c
- ROMFS/px4fmu_common/init.d/rc.mc_apps ~:30-39: under `MC_AT_EN > 0`, nested `param compare -s MC_INDI_EN 1` ->
  `echo "autotune disabled with INDI"`, else `mc_autotune_attitude_control start`. PID path unchanged; boards without
  the INDI module have no MC_INDI_EN, so compare is false and behaviour is unchanged.
- NOT done: the optional once-only INDI-side warning when MC_AT_EN > 0 (note 5c, second part), and the SITL rc test (5e).

## B. Watchdog stamp (MINOR) - done
- McIndiRateControl.cpp:372: `_last_rates_sp_time = hrt_absolute_time()` (receipt time) instead of the publisher stamp.
- RateSetpointWatchdog class semantics unchanged (takes last_rx/now); unit test IndiRateSetpointWatchdog passes.
  The call site has no unit test.

## C. Start refusal PID-after-INDI (MINOR) - not implemented
- Exists: INDI refuses to start if vehicle_torque_setpoint already has a publisher (McIndiRateControl.cpp:70-75).
  mc_rate_control has no such check (and must not be edited), so PID started after INDI is not refused.
- A test needs a SITL shell session: start INDI, start mc_rate_control, assert one publisher; not cheap.

## Build/test
- `make px4_sitl_default` in Docker: OK (294/294). `make tests TESTFILTER=IndiRateSetpointWatchdog`: 1/1 passed.
