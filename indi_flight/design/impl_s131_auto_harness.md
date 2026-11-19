# S131 AUTO-mode bench harness (gate G5 support)

## What changed
- `bench/scenarios.py:193-200`: scenarios `auto_tour` (takeoff 5 m, loiter 10 s, 4-waypoint 20 m square at 5 m, RTL, auto-disarm) and `auto_land10` (takeoff 10 m, loiter 10 s, `commander land` == NAV_LAND, auto-disarm). Mode `auto`, config under key `auto`; RTL_RETURN_ALT 10, NAV_ACC_RAD 2.
- `bench/run_scenario.py`: `mission_upload` (pymavlink mission protocol, MISSION_ITEM_INT, frame 6, home from GLOBAL_POSITION_INT) and `run_auto`/`_run_auto` (~l.703-790); branch right after arm (`if sc["mode"] == "auto"`); `Sim.pump` records heartbeat mode changes (`mode_log`), `GLOBAL_POSITION_INT`, `MISSION_ITEM_REACHED`; phase times in `run.json` `auto_phases`, `mode_log`, `mission`; `takeoff_status` added to LOG_TOPICS (all other required topics were already logged, SDLOG_PROFILE 17 + LOG_TOPICS); `t_land_cmd_us` added to run.json for the offboard land.
- MC_INDI_EN 1 in a params file is now an alias of MC_RATE_CTL_TYPE 1 (`alias_MC_INDI_EN` in run.json).
- `bench/auto_smoke_check.py` + `bench/tests/test_auto_smoke_check.py` (synthetic step 0.08, dip 0.3 m, descent 0.7 m/s: passes).

## Early NAV_LAND (S128-S130): not a runner defect
In the S130 hover ulog the NAV_LAND is at 89.11 s ULog time = window end 85.11 s + 4 s recover, as the runner intends. The "69.5 s" quoted in S130 is 89.11 - 19.62 s (`ulog.start_timestamp`): ULog timestamps are absolute hrt seconds, the analysis subtracted the log start. Same offset explains S128/S129. No runner change needed; `t_land_cmd_us` now records it explicitly. The S130 README "hold window 55-69.5" is therefore wrong, the hold window was 55-85 s (z std 0.015 m of S128 is consistent). Ran on the hover ulog only (POSCTL not re-derived).

## How to run
See `results/auto_smoke_s131/README.md`.

## Results
Both flights ok (README there). Take-off handover step of indi_pos_status.thrust not measurable (module publishes only from 0.1-0.2 s after the edge).

## UNVERIFIED
- Why MIS_TAKEOFF_ALT via CLI was not seen by the navigator; worked around with takeoff altitude in the command.
- Hover-thrust magnitude vs the 0.035 vehicle_thrust_setpoint step (who publishes thrust during rampup).
- One seed, one flight per scenario; no repeat.
- POSCTL early-land explanation checked on the hover log only.
