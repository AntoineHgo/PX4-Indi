# KEY2 review: FW default MC_INDI_XY_VP 3.6 -> 2.4 (S183)

Verdict: AGREE (no blocking finding)

1. Firmware: `git diff -- src` is one line, mc_indi_pos_control_params.yaml (default 3.6 -> 2.4). C++ uses
   `_param_indi_xy_vp.get()` at McIndiPosControl.cpp:601 (declared McIndiPosControl.hpp:221); no literal 3.6,
   clamp or scaling in src/modules/mc_indi_pos_control or src/lib/indi_accel_control. Built
   build/px4_sitl_default/parameters.xml has MC_INDI_XY_VP default="2.4" and bin/px4 (16:32:19) is newer than the yaml (16:31:37).
2. Bench: margins_models.py (XY_GAINS_INDI Kv=2.4 + docstring), g2_outer_model_s164.py help text, tests/test_att_model.py all 2.4.
   `python3 indi_flight/bench/tests/test_att_model.py`: 8/8 PASS (includes test_model_xy_defaults_match_firmware_yaml).
   No other non-results file under indi_flight/bench treats 3.6 as the firmware default.
3. Overrides: no MC_INDI_XY_P / MC_INDI_XY_VP in g5_freeze_s157/params.params, hold_wind_overrides.json,
   g2_freeze_s160/params_fwdef_roll.params, g2_att_freeze_s162/params_base.params, g2_step_s64/indi.params,
   bench/params/*.params, gate_g4.sh, run_scenario.py defaults, scenarios.py, scenario_overrides.py, g2o_fly.sh, g2s_fly.sh.
   Only hits: xy_sweep_s183/queue.sh:13 (explicit sweep values, not used by the freeze8 queue).
   Persistence: runner uses per-run rootfs (<out>/rootfs, run_scenario.py:150, px4 -w) and deletes it at the end (:1376). No shared
   eeprom/parameters file. Residual risk only if a crashed run left <out>/rootfs and the same --out is reused (none found under freeze8_s181/xy_sweep_s183).
Non-blocking notes: stale comment queue.sh line 5 of freeze8_s181 says "firmware defaults 1.2/3.6" (historical; do not copy into the new queue).
The new queue must run against the rebuilt binary (PX4_INDI_BUILD default = build/px4_sitl_default, already rebuilt) and a new results dir (done-files would otherwise skip cells).
Recommend the new queue verify the flown value in each flight.ulg initial_parameters (MC_INDI_XY_VP == 2.4).
