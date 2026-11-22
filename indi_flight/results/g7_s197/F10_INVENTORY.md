# F-10 inventory: indi-fw-pr vs main (gate G7, S197)

Diff: `git diff --name-only main indi-fw-pr`; contents read with `git show indi-fw-pr:<path>`.

Hit regex: project-id pattern from task, plus words `indi_flight`, `indi_project`, `owner`, `gate`, `lesson`, `stage [0-9]` (word-bounded, case-sensitive). `G1`/`G2` not matched.
Comment line = first non-space chars are `//`, `/*`, `*`, or `#`. Ratio = comment lines / lines.

Files: 71; total lines: 18367; comment lines: 3347; total id/word hits: 107.

| Path | Lines | Comment lines | Comment ratio | Id hits |
|---|---:|---:|---:|---:|
| `src/modules/mc_indi_pos_control/McIndiPosControl.cpp` | 1315 | 182 | 13.8% | 20 |
| `src/lib/indi_accel_control/IndiAccelControlTest.cpp` | 1657 | 135 | 8.1% | 10 |
| `src/lib/indi_rate_control/indi_rate_control_test.cpp` | 2400 | 171 | 7.1% | 9 |
| `src/lib/indi_accel_control/indi_accel_control.cpp` | 530 | 86 | 16.2% | 7 |
| `src/lib/indi_accel_control/indi_accel_control.hpp` | 282 | 134 | 47.5% | 6 |
| `src/modules/mc_indi_pos_control/IndiStageMode.hpp` | 108 | 32 | 29.6% | 6 |
| `src/modules/mc_indi_pos_control/McIndiPosControl.hpp` | 367 | 116 | 31.6% | 5 |
| `src/modules/mc_indi_rate_control/IndiInjectionStepTest.cpp` | 338 | 56 | 16.6% | 4 |
| `src/modules/simulation/gz_bridge/GZBridge.cpp` | 1438 | 150 | 10.4% | 4 |
| `src/lib/indi_rate_control/indi_rate_control.cpp` | 493 | 99 | 20.1% | 3 |
| `src/lib/indi_rate_control/indi_rate_control.hpp` | 395 | 200 | 50.6% | 3 |
| `ROMFS/px4fmu_common/init.d-posix/airframes/4040_gz_quad5in` | 86 | 16 | 18.6% | 2 |
| `msg/IndiPosStatus.msg` | 33 | 1 | 3.0% | 2 |
| `msg/IndiRateFeedforward.msg` | 6 | 2 | 33.3% | 2 |
| `src/modules/mc_indi_pos_control/IndiPosInjectionTest.cpp` | 297 | 61 | 20.5% | 2 |
| `src/modules/mc_indi_pos_control/IndiStageModeTest.cpp` | 126 | 4 | 3.2% | 2 |
| `src/modules/mc_indi_rate_control/IndiInjectionStep.cpp` | 78 | 38 | 48.7% | 2 |
| `src/modules/mc_indi_rate_control/IndiInjectionTest.cpp` | 235 | 59 | 25.1% | 2 |
| `src/modules/mc_indi_rate_control/McIndiRateControl.cpp` | 554 | 74 | 13.4% | 2 |
| `src/modules/simulation/gz_bridge/GZBridge.hpp` | 303 | 96 | 31.7% | 2 |
| `src/modules/simulation/gz_bridge/GZMixingInterfaceESC.hpp` | 191 | 51 | 26.7% | 2 |
| `ROMFS/px4fmu_common/init.d-posix/rcS` | 402 | 63 | 15.7% | 1 |
| `ROMFS/px4fmu_common/init.d/rc.mc_apps` | 79 | 28 | 35.4% | 1 |
| `src/modules/mc_indi_pos_control/IndiPosInjection.hpp` | 98 | 61 | 62.2% | 1 |
| `src/modules/mc_indi_rate_control/IndiInjection.hpp` | 97 | 60 | 61.9% | 1 |
| `src/modules/mc_indi_rate_control/IndiMeasuredTorqueTest.cpp` | 373 | 61 | 16.4% | 1 |
| `src/modules/mc_indi_rate_control/IndiRateFeedforwardGate.hpp` | 55 | 45 | 81.8% | 1 |
| `src/modules/mc_indi_rate_control/McIndiRateControl.hpp` | 235 | 90 | 38.3% | 1 |
| `src/modules/mc_indi_rate_control/RateSetpointWatchdog.hpp` | 65 | 43 | 66.2% | 1 |
| `src/modules/mc_indi_rate_control/mc_indi_rate_control_params.yaml` | 330 | 0 | 0.0% | 1 |
| `src/modules/simulation/sim_scenario_player/SimScenarioPlayer.hpp` | 159 | 78 | 49.1% | 1 |
| `ROMFS/px4fmu_common/init.d-posix/airframes/CMakeLists.txt` | 132 | 33 | 25.0% | 0 |
| `boards/px4/sitl/default.px4board` | 98 | 0 | 0.0% | 0 |
| `msg/ActuatorTorqueMeasured.msg` | 11 | 3 | 27.3% | 0 |
| `msg/CMakeLists.txt` | 646 | 59 | 9.1% | 0 |
| `msg/IndiRateStatus.msg` | 28 | 3 | 10.7% | 0 |
| `msg/SimGroundTruth.msg` | 21 | 6 | 28.6% | 0 |
| `msg/SimScheduleApplied.msg` | 27 | 5 | 18.5% | 0 |
| `src/lib/CMakeLists.txt` | 100 | 32 | 32.0% | 0 |
| `src/lib/indi_accel_control/CMakeLists.txt` | 42 | 32 | 76.2% | 0 |
| `src/lib/indi_rate_control/CMakeLists.txt` | 42 | 32 | 76.2% | 0 |
| `src/modules/logger/logged_topics.cpp` | 656 | 73 | 11.1% | 0 |
| `src/modules/mc_indi_pos_control/CMakeLists.txt` | 72 | 34 | 47.2% | 0 |
| `src/modules/mc_indi_pos_control/EkfResetDetect.hpp` | 35 | 7 | 20.0% | 0 |
| `src/modules/mc_indi_pos_control/EkfResetDetectTest.cpp` | 65 | 2 | 3.1% | 0 |
| `src/modules/mc_indi_pos_control/FailsafeSetpoint.hpp` | 76 | 21 | 27.6% | 0 |
| `src/modules/mc_indi_pos_control/FailsafeSetpointTest.cpp` | 117 | 14 | 12.0% | 0 |
| `src/modules/mc_indi_pos_control/IndiPosInjection.cpp` | 138 | 38 | 27.5% | 0 |
| `src/modules/mc_indi_pos_control/Kconfig` | 7 | 0 | 0.0% | 0 |
| `src/modules/mc_indi_pos_control/SetpointExtrapolation.hpp` | 57 | 19 | 33.3% | 0 |
| `src/modules/mc_indi_pos_control/SetpointExtrapolationTest.cpp` | 83 | 5 | 6.0% | 0 |
| `src/modules/mc_indi_pos_control/mc_indi_pos_control_params.yaml` | 141 | 0 | 0.0% | 0 |
| `src/modules/mc_indi_rate_control/CMakeLists.txt` | 94 | 32 | 34.0% | 0 |
| `src/modules/mc_indi_rate_control/IndiInjection.cpp` | 138 | 38 | 27.5% | 0 |
| `src/modules/mc_indi_rate_control/IndiInjectionStep.hpp` | 77 | 49 | 63.6% | 0 |
| `src/modules/mc_indi_rate_control/IndiMeasuredTorque.cpp` | 249 | 46 | 18.5% | 0 |
| `src/modules/mc_indi_rate_control/IndiMeasuredTorque.hpp` | 169 | 86 | 50.9% | 0 |
| `src/modules/mc_indi_rate_control/IndiRateFeedforwardGate.cpp` | 46 | 34 | 73.9% | 0 |
| `src/modules/mc_indi_rate_control/IndiRateFeedforwardGateTest.cpp` | 71 | 34 | 47.9% | 0 |
| `src/modules/mc_indi_rate_control/IndiRateSetpointWatchdogTest.cpp` | 94 | 34 | 36.2% | 0 |
| `src/modules/mc_indi_rate_control/IndiTorqueStampTrackerTest.cpp` | 117 | 37 | 31.6% | 0 |
| `src/modules/mc_indi_rate_control/Kconfig` | 7 | 0 | 0.0% | 0 |
| `src/modules/mc_indi_rate_control/RateSetpointWatchdog.cpp` | 56 | 33 | 58.9% | 0 |
| `src/modules/mc_indi_rate_control/TorqueStampTracker.cpp` | 55 | 33 | 60.0% | 0 |
| `src/modules/mc_indi_rate_control/TorqueStampTracker.hpp` | 66 | 40 | 60.6% | 0 |
| `src/modules/simulation/gz_bridge/GZMixingInterfaceESC.cpp` | 364 | 57 | 15.7% | 0 |
| `src/modules/simulation/gz_bridge/module.yaml` | 290 | 0 | 0.0% | 0 |
| `src/modules/simulation/gz_bridge/server.config` | 29 | 0 | 0.0% | 0 |
| `src/modules/simulation/sim_scenario_player/CMakeLists.txt` | 43 | 32 | 74.4% | 0 |
| `src/modules/simulation/sim_scenario_player/Kconfig` | 6 | 0 | 0.0% | 0 |
| `src/modules/simulation/sim_scenario_player/SimScenarioPlayer.cpp` | 677 | 52 | 7.7% | 0 |

## Top 5 files: example hits (line, matched tokens, first 100 chars)

### `src/modules/mc_indi_pos_control/McIndiPosControl.cpp`

- L57 `A18`: `_indi.setFeedforward(true); // A18: jerk -> body rate feed-forward, consumed by mc_indi_rate_control`
- L96 `D-AF-ALIAS`: `// native-rate force filter before the stage decimates (D-AF-ALIAS)`
- L124 `gate`: `// samples its freshness gate saw, so the integrator reset and can_run agree within a cycle`

### `src/lib/indi_accel_control/IndiAccelControlTest.cpp`

- L305 `D-T10-RESET`: `// D-T10-RESET: an estimator reset must not re-seed the measured force / collective filters with a r`
- L406 `D-STAGE-STALE`: `// D-STAGE-STALE (a): f_b replaced by the delayed modelled specific force: t_c = a_ref - g, no recur`
- L666 `D-T10-RESET`: `// D-T10-RESET: a step of a_ff right after resetJerkHistory() is not differentiated into jerk`

### `src/lib/indi_rate_control/indi_rate_control_test.cpp`

- L706 `D-S3-LANDED`: `// the feedback torque is ramped (D-S3-LANDED): one slew step of the modelled torque`
- L1254 `D-S3-LANDED`: `// the first airborne feedback torque is one slew step of the ramp (D-S3-LANDED), the blend has no m`
- L1288 `D-S3-LANDED`: `// asserts (G7(b) M19): maybe_landed freezes the slow blend integrator (header, D-S3-LANDED): the bl`

### `src/lib/indi_accel_control/indi_accel_control.cpp`

- L156 `D-GAP`: `// D-GAP: model path = commanded collective (u_model = c * k_cmd). Measured path = the measured mean`
- L159 `A16`: `// A16: b is held, never reset`
- L296 `D-ALTCTL-Z`: `// D-ALTCTL-Z: the stock thrust direction must be finite and clearly upward`

### `src/lib/indi_accel_control/indi_accel_control.hpp`

- L37 `indi_project`: `* Outer-loop (acceleration) INDI with jerk feedforward, see indi_project/plan/s8_impl_spec.md sec. 2`
- L109 `A14`: `bool accel_only{false};    ///< start at a_ref (A14): no p/v terms, a_c = a_ref, p and v are not req`
- L110 `D-ALTCTL-Z`: `/// D-ALTCTL-Z: only the collective is INDI, the direction is thrust_dir (stock thrust vector, NED, `

