# G7(f) instructions checklist, branch `indi-fw-pr` vs `main`

Reviewer pass, S196. Read-only (git show/archive of the branch); 73 changed files, 14.3k added lines under src/.

## Instruction files applied

Changed paths: `msg/`, `src/lib/indi_*`, `src/modules/mc_indi_*`, `src/modules/simulation/{gz_bridge,sim_scenario_player}`, `src/modules/logger/logged_topics.cpp`, `ROMFS/`, `boards/px4/sitl`, Kconfig files.

| File | applyTo match | Applied |
| --- | --- | --- |
| `.github/instructions/code-review.instructions.md` | src/**, msg/**, boards/** | yes |
| `.github/instructions/parameters.instructions.md` | src/**, ROMFS/**, boards/** | yes |
| `.github/instructions/control.instructions.md` | src/modules/mc_*control*/** | yes |
| `.github/instructions/messages.instructions.md` | msg/** | yes |
| `.github/instructions/simulation.instructions.md` | src/modules/simulation/** | yes |
| `.github/instructions/system.instructions.md` | src/modules/logger/** | yes (logged_topics.cpp, 3 lines only) |
| `.github/instructions/ci-build.instructions.md` | **/Kconfig | yes (3 Kconfig files) |
| board-addition, drivers, estimation, docs.en | no match (boards/px4/sitl is a 3-line `default.px4board` edit, not a board addition; no docs/en in the diff) | no |

Also read: `docs/en/concept/navigation_terminology.md`, "Guidelines for Contributors" in `navigation_terminology_advanced.md`, `docs/en/uorb/uorb_documentation.md` (referenced by the contributor guidelines for `[@frame]`/unit tags). Nested AGENTS.md: none along the changed paths (only `docs/scripts/...` and `src/modules/mavlink/mavlink/`). Root AGENTS.md style rule checked with astyle (see row S1).

## Checklist

Paths relative to the branch tree. P = `parameters.instructions.md`, M = `messages.instructions.md`, CR = `code-review.instructions.md`.

| # | Rule (source) | Verdict | Evidence |
| --- | --- | --- | --- |
| P1 | One owner per parameter, named by what the module does (P:9) | PASS | MC_INDI_* owned by the two INDI modules, SIM_GZ_* by gz_bridge |
| P2 | Consume other module's result on uORB, not its thresholds (P:10) | PASS | pos control reads `MPC_*` shared vehicle config (`McIndiPosControl.hpp:223-232`), existing practice per P:10 |
| P3 | No two params with the same meaning in different modules (P:11) | FINDING MAJOR | `MC_INDI_XY_P` "Replaces MPC_XY_P", `MC_INDI_XY_VP` "Replaces MPC_XY_VEL_P_ACC" (`mc_indi_pos_control_params.yaml` MC_INDI_XY_P, MC_INDI_XY_VP) while the other MPC_* gains are still read |
| P4 | param_translation only for released params (P:12-13) | PASS | no parameter removed or renamed from main; no translation needed |
| P5 | Parameter name length, prefix, group | PASS | all new names <= 16 chars (longest MC_INDI_PINJ_AMP, MC_INDI_INJ_FMIN, SIM_GZ_ERPM_LOSS) |
| P6 | module.yaml format: type, default, min/max, decimal, increment, reboot_required | PASS | yaml parsed: every float/int32 has min, max, default; every float has decimal; boot-time params carry `reboot_required` (MC_INDI_POS_EN, MC_INDI_EN, SIM_GZ_ESC_FB, ERPM_POL, DLY_*) |
| P7 | Units given for physical quantities (P:19 unit field) | FINDING MINOR | no `unit` on MC_INDI_G1_R/P/Y, G2_Y (rad/s^2 per normalised torque, stated only in long), MC_INDI_DT_MAX, MC_INDI_LND_SLEW (1/s), SIM_GZ_ERPM_DRP |
| P8 | `long` omits what short/unit/min/max/options already say (P:19) | FINDING MINOR | MC_INDI_K_R/P/Y long "Closed loop roll rate tracking bandwidth" restates short; MC_INDI_INJ_AMP/INJ_RAMP long restates short and unit |
| P9 | Option detail in labels, one `Label: effect.` line per option, never re-list options (P:20) | FINDING MINOR | MC_INDI_ID_OK is int32 0/1 with `0:`/`1:` lines in long, should be a boolean or enum with labels (`mc_indi_rate_control_params.yaml` MC_INDI_ID_OK); enums INJ_AX, PINJ_PT, ESC_FB use labels: PASS |
| P10 | Drop rationale that does not change the value picked, "Note that", "This parameter" (P:21) | FINDING MINOR | long rationale in MC_INDI_G2_Y (484 chars), MC_INDI_ACT_BLD (372), MC_INDI_INJ_PT (374), SIM_GZ_EC_SIGNED (463), SIM_GZ_IMU_NSC (340); no "Note that"/"This parameter" found (grep) |
| P11 | Stock phrases "Set to 0 to disable.", "Only used when X is enabled." (P:22) | PASS | used in MC_INDI_POS_LPF, POS_TB, G2_Y, YAW_CUT, ERPM_*; SIM_GZ_ERPM_* use "Used by SIM_GZ_ESC_FB 2" (non-stock wording, trivial) |
| P12 | No symbols as words (`<=`, `=`, `/` for "or") (P:23) | FINDING MINOR | `/` and `=` as arithmetic in MC_INDI_G2_Y long ("G2 / MC_INDI_G1_Y", "27 / 205 = 0.13 s"), "0.5x", "2x" in MC_INDI_ID_OK and ACT_TC, "u = c + d" in MC_INDI_INJ_AX; "G2"/"G1" used as abbreviations instead of the parameter names; "D-GAP"/"D-F7" style tags only in msg/comments |
| P13 | Prose is one paragraph, no mid-sentence newlines (P:24) | FINDING MAJOR | newlines inside prose in MC_INDI_EN, MC_INDI_W_MAX (also a blank line), MC_INDI_ACT_TC, MC_INDI_INJ_AX, MC_INDI_INJ_PT (`mc_indi_rate_control_params.yaml`); `|` style wrapped lines reach QGC unchanged. gz_bridge module.yaml new params are single scalars: PASS |
| P14 | Airframe defaults via `param set-default` | PASS | `4040_gz_quad5in` uses set-default only; id 4040 free on main (4001-4021 used); added to airframes/CMakeLists.txt |
| P15 | Airframe file self-contained, no reference to files outside the PR | FINDING MINOR | `4040_gz_quad5in` header cites `indi_flight/sim/models/quad5in` and `indi_flight/design/ref_airframe_model.md`; `indi_flight/` is not on the branch (0 files), the model it needs is not shipped |
| M1 | Backwards compatibility, no change to existing messages (M:9) | PASS | 6 new .msg only; no existing message edited; added to msg/CMakeLists.txt in alphabetical place |
| M2 | `timestamp` publication, `timestamp_sample` near physical sample (M:10) | PASS | ActuatorTorqueMeasured, IndiRateStatus, SimGroundTruth carry `timestamp_sample`; IndiPosStatus/IndiRateFeedforward are derived status without a physical sample |
| M3 | Include `device_id` (M:10) | FINDING MINOR | `ActuatorTorqueMeasured.msg` is derived from esc_status, no `device_id`; judged not applicable to a computed topic, listed for the owner |
| M4 | Do not version messages (M:11) | PASS | no `MESSAGE_VERSION` anywhere |
| M5 | uORB doc standard: leading description block, `[unit]` and `[@frame]` tags in field comments (uorb_documentation.md:63-130; contributor guideline) | FINDING MINOR | IndiPosStatus, IndiRateStatus, IndiRateFeedforward, ActuatorTorqueMeasured start with the timestamp line, no mandatory short description header; units written as `(m/s^2)` / `rad/s` prose instead of `[m/s^2]`, no `[@frame NED]`/`[@frame FRD]` (frame given only in prose). SimGroundTruth and SimScheduleApplied follow the standard: PASS |
| M6 | Field and topic naming (snake_case fields, CamelCase file, accurate names) | PASS | `a_c`, `t_f`, `q_d`, `nu`, `omega_ff` terse but defined in comments; SimGroundTruth `x,y,z,vx,vy,vz` match stock local position |
| M7 | Accurate comments (CR:24) | FINDING MINOR | `IndiRateStatus.msg:4` says "published by mc_rate_control only while MC_RATE_CTL_TYPE selects INDI"; the publisher is `mc_indi_rate_control` and the selector is `MC_INDI_EN` (`MC_RATE_CTL_TYPE` exists nowhere on the branch) |
| M8 | Parameter UX: every new param is a burden (M:12) | FINDING MINOR | 30 MC_INDI_* rate + 14 MC_INDI_* pos + 17 new SIM_GZ_* params; the INJ/PINJ bench-injection set (12 params) ships to flight users; consider keeping it behind the board config or documenting as bench only (it is labelled "Bench and system identification only") |
| L1 | New topics logged (system:logger, CR ecosystem) | PASS | `add_optional_topic` for actuator_torque_measured, indi_pos_status, indi_rate_feedforward, indi_rate_status (`logged_topics.cpp`); sim topics not in default set |
| C1 | Control: NaN checked with PX4_ISFINITE before magnitude checks (control:11) | PASS | spot check: `PX4_ISFINITE` used in McIndiPosControl/McIndiRateControl; failure path commands level attitude |
| C2 | Control: prefer setpoint smoothing over output filtering, no circular dependency (control:9-12) | PASS | rate-setpoint lead and setpoint extrapolation are setpoint-side; output-side filters limited to configurable YAW_CUT (default documented) |
| C3 | Control: yaw edge cases, heading reset propagated (control:13) | PASS | `heading_reset_counter` handled: McIndiPosControl.cpp:1209-1210, 1245-1247, EkfResetDetect |
| C4 | Control allocation motor index mapping (control:15) | PASS | IndiMeasuredTorque uses motor index i = bit i, Motor1 = bit 0 (`ActuatorTorqueMeasured.msg`), tests IndiMeasuredTorqueTest |
| S1 | Formatting: `make check_format` astyle (CR:27, AGENTS.md) | PASS | astyle 3.1 with `Tools/astyle/astylerc --dry-run` on all branch .cpp/.hpp under src/: no file reformatted. clang-tidy not run |
| S2 | Type safety, double promotion (CR:19) | PASS | spot check: printf casts `(double)` in tests; no hrt arithmetic on 32-bit |
| S3 | Magic numbers need a named constant or justification (CR:22) | FINDING MINOR | `McIndiRateControl.cpp:311` `constrain(dt, 0.000125f, 0.02f)`; frozen-command threshold 0.02 in the MC_INDI_ERPM_FRZ description is hardcoded; `500_ms` and "0.5 s" in `McIndiPosControl.cpp:486-490`; check the pos/rate `.cpp` for similar inline limits |
| S4 | Framework reuse: PX4_ERR/WARN/INFO, no printf in modules (CR:23) | PASS | `printf` only in unit tests (IndiRateControlTest, margins, staircase); modules use PX4_*; no std::string/vector in modules (std::vector only in the test margin helper) |
| S5 | Warnings not per cycle (log spam) | PASS | rate-setpoint warn gated by watchdog `wd.warn`; stage degraded warns once (`_degraded_warned`) |
| S6 | Module structure: ModuleBase, ScheduledWorkItem/WorkItem, PRINT_MODULE_USAGE, `extern "C"` main, no extra threads (system:12) | PASS | all three modules (`McIndiRateControl.cpp:45,531-553`, `McIndiPosControl.cpp:45,1293-1314`, `SimScenarioPlayer.cpp:45,656-676`) use the ModuleBase::Descriptor pattern and work queues |
| S7 | Kconfig + CMake conventions, board enable (ci-build; CR architecture) | PASS | `menuconfig MODULES_*` with `default n` and `depends on`, `px4_add_module` with MODULE_CONFIG, gtests registered, boards/px4/sitl/default.px4board enables 3 modules only; libs are `EXCLUDE_FROM_ALL` |
| S8 | Start-up: rc.mc_apps behaviour on boards without the module | PASS | `param compare -s MC_INDI_EN 1` false when the param is absent, PID starts (comment in `rc.mc_apps`); autotune skipped with INDI |
| S9 | Start-up: INDI position module has no fallback if it fails to start | FINDING MINOR | `rc.mc_apps`: "no stock fallback; if the INDI module fails to start there is no position controller" (owner decision, memory: no PID fallback). Consistent with project direction, flagged as a flight-safety review point |
| S10 | License header and `#pragma once` on new files | FINDING MINOR | 8 new files in mc_indi_pos_control have no BSD license header: `SetpointExtrapolation.hpp`, `EkfResetDetect.hpp`, `FailsafeSetpoint.hpp`, `IndiStageMode.hpp` and the four matching `*Test.cpp`; `#pragma once` present on all headers |
| S11 | File and test naming consistent | FINDING MINOR | `src/lib/indi_rate_control/indi_rate_control_test.cpp` is snake_case while the other new tests are `*Test.cpp` (`IndiAccelControlTest.cpp`) |
| S12 | Line length (astylerc has no limit, PX4 style 120) | FINDING MINOR | 226 added non-comment lines exceed 120 columns (tabs counted as 8); astyle does not break them. Mostly long expressions in tests and yaml `long` strings |
| S13 | GPS to GNSS in new code (CR:24) | FINDING MINOR | new parameter `SIM_GZ_GPS_DLY` and log texts "GPS_DLY" in `GZBridge.cpp` (PX4_INFO lines); should be `SIM_GZ_GNSS_DLY` (parameter renaming costs nothing before release) |
| SIM1 | Keep gz_bridge generic, vehicle-specific logic in plugins (sim:10) | FINDING MINOR | `SIM_GZ_ESC_FB` long names `rotor_N_joint` and "rotorVelocitySlowdownSim 10" (model-specific details in a generic param description); delay lines, eRPM model and vibration are generic: PASS |
| SIM2 | Noise/physics fidelity (sim:9) | PASS | GNSS delay ring buffer keeps `timestamp_sample`; IMU delay keeps sample time; drop probability is Bernoulli (stated) |
| SIM3 | gz-transport only, no ROS2 (sim:11) | PASS | no ROS includes in the diff |
| SIM4 | Library generic/specific boundary (sim:13) | PASS | `GZMixingInterfaceESC` gets the delay line, no vehicle logic |
| SIM5 | SITL-only module and message gating | PASS | sim_scenario_player and the two Sim* messages are documented "SIMULATION ONLY, never published on real hardware"; module enabled only in sitl board |
| N1 | Use heading only for body-x direction, course for ground motion, bearing only point-to-point; no new terms (advanced:contributors) | PASS | `heading` only from `vehicle_local_position.heading`/`delta_heading`/`heading_reset_counter` (stock names); setpoints named `yaw` (allowed, terminology.md:55); no `course`/`bearing`/`track` identifier introduced; `sensor_gnss.course` assignment in GZBridge.cpp:1096 is the stock field and uses `atan2(vel_east, vel_north)` (ground course, correct) |
| N2 | Never bare "drift"; "desired track" for intended path (advanced:contributors) | FINDING MINOR | `IndiAccelControlTest.cpp:973` test name `NoDriftAfterResetWithoutHold` and blend/estimator "drift" in comments mean numerical state drift, not the navigation term; rename to "NoStateChange..." to avoid the reserved word |
| N3 | State reference, unit and range, `[@frame]`/`[@range]` tags in field comments (advanced:contributors) | FINDING MINOR | same cause as M5: no `[@frame]` tags on IndiPosStatus/IndiRateStatus/IndiRateFeedforward; SimGroundTruth has them. No heading/course fields in the new messages, so no true-north statement needed |
| N4 | Yaw as rotation about vertical axis vs heading direction (terminology.md:55-57) | PASS | MC_INDI_*_Y/yaw rate/yaw torque used as rotation (allowed); `q_d` "from the commanded thrust vector and yaw" is the heading setpoint (yaw) |
| N5 | Sideslip only for airflow angle | N.A. | no sideslip identifier added (grep) |
| N6 | Cross-track convention | N.A. | not used |
| D1 | Docs only in docs/en | N.A. | no docs in the branch |

Counts: 53 rows: 29 PASS, 21 FINDING (2 MAJOR, 19 MINOR), 3 N.A.

## Findings by severity

### MAJOR (violates a stated must-rule)

1. P3, `parameters.instructions.md:11`: `MC_INDI_XY_P` and `MC_INDI_XY_VP` duplicate the meaning of `MPC_XY_P` and `MPC_XY_VEL_P_ACC` in another module while the module reads the other MPC_* gains. Fix: reuse `MPC_XY_P`/`MPC_XY_VEL_P_ACC` (shared vehicle configuration) or document the INDI-only gains as a split concept with distinct names and descriptions, owner decision.
2. P13, `parameters.instructions.md:24`: mid-sentence newlines inside `long` in MC_INDI_EN, MC_INDI_W_MAX, MC_INDI_ACT_TC, MC_INDI_INJ_AX, MC_INDI_INJ_PT (`mc_indi_rate_control_params.yaml`). Fix: join each into one single-line (or quoted) scalar paragraph; keep newlines only between per-option lines.

### MINOR

- P7: add `unit` to MC_INDI_G1_*/G2_Y, DT_MAX, LND_SLEW (or state "normalised" in short).
- P8: drop `long` where it restates short or unit (K_R/P/Y, INJ_AMP, INJ_RAMP, G1_*).
- P9: make MC_INDI_ID_OK a boolean (or enum with labels).
- P10, P12: shorten rationale-heavy `long` text, remove "G2 / G1", "27 / 205 = 0.13 s", "0.5x", "u = c + d"; name parameters in full.
- P15: remove `indi_flight/...` references from the airframe header, or ship the model it needs.
- M3: confirm no `device_id` for the computed ActuatorTorqueMeasured (likely N.A.).
- M5/N3: add the mandatory description block and `[unit]`/`[@frame NED|FRD]` tags to the four Indi/ActuatorTorque msg files.
- M7: fix `IndiRateStatus.msg:4` (publisher `mc_indi_rate_control`, selector `MC_INDI_EN`).
- M8: reduce the shipped bench-injection parameter set or keep it clearly bench only.
- S3: name the 0.000125f/0.02f dt limits, the 0.02 frozen-command threshold and the 500 ms degraded timeout.
- S9: flight-safety review point, no stock fallback if INDI pos fails to start (owner decision, consistent with project direction).
- S10: add the BSD license header to the 8 new mc_indi_pos_control files that lack it.
- S11: rename `indi_rate_control_test.cpp` to `IndiRateControlTest.cpp` (update CMake).
- S12: wrap the 226 non-comment lines over 120 columns.
- S13: rename `SIM_GZ_GPS_DLY` to `SIM_GZ_GNSS_DLY` (and log text).
- SIM1: move `rotor_N_joint`/`rotorVelocitySlowdownSim` model detail out of the SIM_GZ_ESC_FB description.
- N2: rename `NoDriftAfterResetWithoutHold`, avoid bare "drift".

## Not reviewed / limits

- clang-tidy not run. No docs. Magic-number review (S3) and control rules (C1-C4) were spot checks, not a line-by-line pass over 14k lines.
- Line counts for S10 and S12 come from greps on the branch snapshot (tabs as 8 columns).
- Param descriptions parsed with PyYAML on the branch yaml files (pos 14, rate 30, gz_bridge new ones); units/min/max/decimal were checked mechanically, wording by reading.
