# G7 S246 leftover ID grep (INDI firmware)

Repository: /home/ahugo/Documents/Drotek/Codes/PX4-Indi (branch feat/indi-flight)
Read-only scan. No files edited besides this output.

## Scope

- Firmware files (51 files, recursive):
  - src/lib/indi_rate_control/ (all files)
  - src/lib/indi_accel_control/ (all files)
  - src/modules/mc_indi_rate_control/ (all files)
  - src/modules/mc_indi_pos_control/ (all files)
  - msg/IndiPosStatus.msg, msg/IndiRateFeedforward.msg, msg/IndiRateStatus.msg
  - ROMFS/px4fmu_common/init.d-posix/airframes/4040_gz_quad5in
    (no 4040* airframe exists under ROMFS/px4fmu_common/init.d/airframes)
- src/modules/simulation/gz_bridge/: only '+' lines versus main (839 added lines).
  Line numbers in the gz hits are new-file line numbers.

## Commands run

```
# file list
find src/lib/indi_rate_control src/lib/indi_accel_control src/modules/mc_indi_rate_control src/modules/mc_indi_pos_control -type f
ls msg/*.msg | grep -i indi
find ROMFS/px4fmu_common/init.d*/airframes -name '4040*'

# firmware scan (grep is ugrep here, so /usr/bin/grep was used)
echo "$FILES" | xargs /usr/bin/grep -n -E 'D-[A-Z0-9]+(-[A-Z0-9]+)*'
echo "$FILES" | xargs /usr/bin/grep -n -E '\b(A|S|K|Q|F|T|H|RC|O)[0-9]{1,3}\b|\b[FO]-[0-9]+\b'
echo "$FILES" | xargs /usr/bin/grep -n -E '\bG[3-8]\b|G[0-9]\([a-z]\)'
echo "$FILES" | xargs /usr/bin/grep -n -E 'indi_flight|indi_project'
echo "$FILES" | xargs /usr/bin/grep -n -i -E '\b(owner|gate|gates|freeze|frozen|lesson|session|stage|anomaly|errata|review)\b'

# gz_bridge: '+' lines with new-file line numbers
git diff main -U0 -- src/modules/simulation/gz_bridge | awk '/^\+\+\+ /{f=substr($2,3)} /^@@/{split($3,a,","); n=substr(a[1],2)+0; next} /^\+/{print f":"n": "substr($0,2); n++}' > <scratch file, deleted afterwards>
grep -n -E '<pattern 1-4>' <scratch>
grep -n -i -E '\b(owner|gate|gates|freeze|frozen|lesson|session|stage|anomaly|errata|review)\b' <scratch>
```

## Count table

Total = all hits. LIKELY-ID and LIKELY-OK are counts of the total.

| Pattern | Firmware hits | gz_bridge '+' hits | Total | LIKELY-ID | LIKELY-OK |
|---|---|---|---|---|---|
| 1. decision ids `D-...` | 0 | 1 | 1 | 1 | 0 |
| 2. ids `\b(A\|S\|K\|Q\|F\|T\|H\|RC\|O)[0-9]{1,3}\b` and `[FO]-n` | 26 | 2 | 28 | 5 | 23 |
| 3. gate refs `G3-G8`, `G[0-9](x)` | 0 | 0 | 0 | 0 | 0 |
| 4. paths `indi_flight\|indi_project` | 0 | 1 | 1 | 1 | 0 |
| 5. project words (case-insensitive) | 68 | 4 | 72 | 0 | 72 |
| **Total** | 94 | 8 | 102 | 7 | 95 |

## LIKELY-ID hits (7)

Files: 3 in src/modules/mc_indi_pos_control/ (one hit each) and 3 in src/modules/simulation/gz_bridge/ (GZBridge.cpp has 2 hits, GZBridge.hpp 1, GZMixingInterfaceESC.hpp 1). Total 6 files.

- src/modules/mc_indi_pos_control/EkfResetDetect.hpp:4: ` * Detection of a change of the vehicle_local_position estimator reset counters (T10). Pure, header only.` (task id T10 in comment)
- src/modules/mc_indi_pos_control/FailsafeSetpoint.hpp:4: ` * Failsafe trajectory setpoint of the INDI position module (T5). Pure function, no module state, so it i` (task id T5 in comment)
- src/modules/mc_indi_pos_control/SetpointExtrapolation.hpp:4: ` * Extrapolation of a held trajectory setpoint of the INDI position module (probe F2). The sender pu` (probe id F2 in comment)
- src/modules/simulation/gz_bridge/GZBridge.cpp:686: `// One tone pair referred to the IMU (D-VIB-HOOK): the net imbalance line at the mean rotor speed (1P, ro` (decision id D-VIB-HOOK)
- src/modules/simulation/gz_bridge/GZBridge.hpp:175: `// SIM_GZ_DLY_IMU delay line (hook A2), one ring per IMU instance, shared mutex (gz transport callbacks ` (hook id A2 in comment)
- src/modules/simulation/gz_bridge/GZMixingInterfaceESC.hpp:155: `// SIM_GZ_DLY_ACT delay line (hook A1). Only touched from updateOutputs(), which runs inside` (hook id A1 in comment)
- src/modules/simulation/gz_bridge/GZBridge.cpp:644: `// Base stddev = SDF values in indi_flight/sim/staged/quad5in_base_model_a14.sdf (gyro lines ~186-198, ac` (workspace path in comment)

## LIKELY-OK hits (95), grouped per word

- **T0** (pattern 2, 23 hits, all firmware): test timestamp variable name. Examples:
  - src/modules/mc_indi_rate_control/IndiRateFeedforwardGateTest.cpp:37: `static constexpr uint64_t T0 = 10000000;` (test timestamp variable)
  - src/modules/mc_indi_rate_control/IndiRateSetpointWatchdogTest.cpp:38: `static constexpr uint64_t T0 = 10000000;` (test timestamp variable)
  - src/modules/mc_indi_rate_control/IndiRateFeedforwardGateTest.cpp:41: `EXPECT_TRUE(IndiRateFeedforwardGate::allow(true, T0, T0, ...` (test timestamp argument)
- **owner** (pattern 5, 35 hits, all firmware): license header boilerplate. Examples:
  - src/lib/indi_accel_control/CMakeLists.txt:23: `# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,` (license header boilerplate)
  - src/modules/mc_indi_pos_control/McIndiPosControl.cpp:23: ` * COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,` (license header boilerplate)
  - src/modules/mc_indi_rate_control/TorqueStampTracker.hpp:23: ` * COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,` (license header boilerplate)
- **stage** (pattern 5, 11 hits, all firmware): INDI control stage term. Examples:
  - msg/IndiPosStatus.msg:4: `float32[3] a_c # commanded acceleration, input of the INDI stage, including the bench excitation (m/s^2)` (INDI control stage term)
  - src/modules/mc_indi_pos_control/Kconfig:7: `stock position control followed by an acceleration INDI stage.` (INDI control stage term)
  - src/modules/mc_indi_pos_control/mc_indi_pos_control_params.yaml:158: `0: Stage input` (INDI control stage term)
- **freeze / frozen** (pattern 5, 26 hits: 22 firmware + 4 gz_bridge): frozen rotor or output state. Examples:
  - src/modules/mc_indi_rate_control/IndiMeasuredTorque.cpp:103: `_samples[motor].frozen = false;` (frozen rotor state)
  - src/modules/mc_indi_rate_control/IndiMeasuredTorque.hpp:117: `Time in s that a bit-identical rpm has to persist ... to count as frozen` (frozen rotor detection)
  - src/modules/simulation/gz_bridge/module.yaml:174: `Motors with frozen eRPM telemetry` (frozen rotor telemetry)
- Other firmware words: none (no hits for gate, gates, lesson, session, anomaly, errata, review).
- Pattern 1 and 4 (firmware): no LIKELY-OK hits.
- Pattern 3: no hits anywhere.
