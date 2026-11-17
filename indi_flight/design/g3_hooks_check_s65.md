# G3 robustness hooks: existence check (S65)

Read-only search. Paths relative to the repo root `/home/ahugo/Documents/Drotek/Codes/PX4-Indi`.
Gate draft checked: `indi_flight/design/gates_g3_g8_draft_s64.md` lines 30-45.
Scope: `src/modules/simulation/gz_bridge/`, `indi_flight/bench/scenarios.py`, `indi_flight/bench/run_scenario.py`,
`indi_flight/DECISIONS.md`, `indi_flight/JOURNAL.md`. `indi_flight/bench/model_variant.py` was not searched (not in the
S65 call budget). `indi_flight/sim/` was searched only for IMU noise in the staged SDF.

## Hook status

| hook | status | evidence (file:line) | parameter or CLI name | how set per run | sim time? |
|---|---|---|---|---|---|
| (a) added loop delay 0-10 ms on actuator or sensor path | ABSENT | No sim-side delay on IMU, GNSS, or actuator path in `GZBridge.cpp` or `GZMixingInterfaceESC.cpp`. Only `ScheduleDelayed(10_ms)` at `GZBridge.cpp:201` (module scheduling, not an injector). `scenarios.py` and `run_scenario.py` have no loop-delay key. `DECISIONS.md:268` mentions a *measured* 400 Hz loop delay, not an injector. | none | none | n/a |
| (b) vibration scale x[1, 5] on IMU | PARTIAL | Sinusoidal per-rotor IMU vibration: `GZBridge.cpp:623` `addRotorVibration`, called for IMU instance 0 at `GZBridge.cpp:681`, uses gz message stamps (`GZBridge.cpp:662`, sim time). Amplitude params in `module.yaml:145` (SIM_GZ_VIB_ACC), `:158` (SIM_GZ_VIB_GYR), `:170` (SIM_GZ_VIB_RPM, rotor speed at which the amplitudes apply). Scale x3 example in `scenarios.py:160` (ACC=3.0, GYR=0.15). Scale is a linear change of the two amplitudes. Wideband Gaussian IMU noise is an SDF `<noise>` block (`indi_flight/sim/staged/quad5in_base_model_a14.sdf:143-220`) with no scale hook found in the bridge. | `SIM_GZ_VIB_ACC`, `SIM_GZ_VIB_GYR`, `SIM_GZ_VIB_RPM`; CLI `run_scenario.py --vib-acc`, `--vib-gyr` (`:607-608`) | CLI sets env `PX4_PARAM_SIM_GZ_VIB_ACC/GYR` (`run_scenario.py:692-695`), only when a value > 0 and only with `SIM_GZ_ESC_FB >= 1` (joint speeds needed). Scenario dict `sim_params` (`scenarios.py:160`). | yes (rotor-phase integration on message stamps). Noise scale: UNVERIFIED for the SDF path. |
| (c) GNSS latency 80-250 ms, matched / mismatched EKF2_GPS_DELAY | PARTIAL (param side only) | Latency: ABSENT. The GNSS sample is stamped with current sim time (`GZBridge.cpp:972` `sensor_gnss.timestamp_sample = timestamp`). `run_scenario.py:610-612` help text says the gz GNSS "has no latency but stamps no sample time", so the bench compensates with a fixed EKF delay. Mismatch param: `run_scenario.py:610-612, 696-698` sets `SENS_GNSS0_DELAY` (stock 110 ms, D-s8-gnss-delay). Its `DECISIONS`/`JOURNAL` references were not separately grepped. | `SENS_GNSS0_DELAY` (CLI `--gnss-delay`, ms). Not `EKF2_GPS_DELAY`: name used by the gate draft not seen in code (UNVERIFIED whether it is an alias). | CLI `--gnss-delay N` -> env `PX4_PARAM_SENS_GNSS0_DELAY` (`run_scenario.py:696-698`), meta `gnss_delay` in run.json. | Param: applied by PX4 at start (sim time for the estimator). Latency injection: none. |
| (d) telemetry latency 0-3 frames | EXISTS | `GZMixingInterfaceESC.cpp:161-163` delay line of `ERPM_DELAY_LEN = 9` frames; latency read at `GZMixingInterfaceESC.hpp:66-67` and clamped to 0-8. Param in `module.yaml:116-124` (int 0-8, default 0, reboot_required). Active only with `SIM_GZ_ESC_FB = 2` (`run_scenario.py:689`, v2 sim). Scenario `lat` = 2 frames at `scenarios.py:152` (V3). | `SIM_GZ_ERPM_LAT` (frames) | Scenario `sim_params` (`scenarios.py:152`), or env `PX4_PARAM_SIM_GZ_ERPM_LAT`, or `--params FILE` (`run_scenario.py:595, 700`; exact loop over sim_params UNVERIFIED). Set at boot (reboot_required). | yes: a frame is one ESC output period (`GZMixingInterfaceESC.cpp:140-150`, sim-stepped). |
| (e) telemetry loss / frozen values, seeded dropout generator | PARTIAL | Dropout: `SIM_GZ_ERPM_DRP` (`module.yaml:105-111`) with `uniformRandom() < p` at `GZMixingInterfaceESC.cpp:151`. Seed is FIXED in code (`GZMixingInterfaceESC.hpp:131`, `_random_state{0x12345678u}`): repeatable run to run but NOT controlled by a per-run seed. The gz `--seed` (`run_scenario.py:226`) seeds gz, not this generator. Total loss and frozen hold: `SIM_GZ_ERPM_LOSS` bitmask (`module.yaml:126-133`, read at runtime) makes every frame of the motor fail, holding the last value (`GZMixingInterfaceESC.cpp:149`, `_erpm_last_rpm` in `hpp:129`) and incrementing esc_errorcount. Timed loss scenario keys `erpm_loss` at `scenarios.py:158-159` (3 s and 2.25 s). Generic runtime Stuck injection exists for GNSS and VIO (`GZBridge.hpp:197-198`, `GZBridge.cpp:993`) and ESC (`FailureInjection.cpp:168`), via the failure_injection lib (`src/lib/failure_injection/FailureInjection.hpp:118`). Frozen detector `D-S3-FROZEN` (`DECISIONS.md:363-371`) is a detector, not an injector. | `SIM_GZ_ERPM_DRP` (0-1 prob.), `SIM_GZ_ERPM_LOSS` (bitmask 0-255); scenario `erpm_loss` | `run_scenario.py:690` sets `PX4_PARAM_SIM_GZ_ERPM_DRP` from `--erpm-drop` (`:609`). `scenarios.py:153, 158-159`. Timing driver for `erpm_loss` in `run_scenario.py` NOT verified. | yes for the held values and dropout (per ESC frame). Duration control of the timed loss: UNVERIFIED. |

## Parameter list (gz_bridge module.yaml / parameters.yaml)

Checked: `src/modules/simulation/gz_bridge/module.yaml` and `parameters.yaml` (grep for `SIM_` keys). `*_params.c` files were not searched.

- Telemetry / ESC: `SIM_GZ_ESC_FB` (:81), `SIM_GZ_ERPM_POL` (:96), `SIM_GZ_ERPM_DRP` (:105), `SIM_GZ_ERPM_LAT` (:116), `SIM_GZ_ERPM_LOSS` (:126), `SIM_GZ_THR_SC` (:135), `SIM_GZ_EC_SIGNED` (:180)
- Vibration: `SIM_GZ_VIB_ACC` (:145), `SIM_GZ_VIB_GYR` (:158), `SIM_GZ_VIB_RPM` (:170)
- Sensor enables: `SIM_GZ_EN`, `SIM_GZ_EN_GPS`, `SIM_GZ_EN_IMU`, `SIM_GZ_EN_BARO`, `SIM_GZ_EN_MAG`, `SIM_GZ_EN_ODOM`, `SIM_GZ_EN_ASPD`, `SIM_GZ_EN_FLOW`, `SIM_GZ_EN_LIDAR` (parameters.yaml)
- No parameter exists for IMU/actuator loop delay, GNSS sample latency, or IMU noise scale.

## Must still be built

1. Loop delay (a): a sim-side delay line on the IMU publish path (or actuator command path) with a 0-10 ms param in 1.25 ms steps, stamped in sim time. Nothing in the bridge does this; `failure_injection` `Delayed` (`FailureInjection.hpp:68`) is only a name in the enum, not verified for these topics (UNVERIFIED).
2. GNSS latency (c): a latency buffer in `GZBridge` for `sensor_gnss` (80-250 ms) so the EKF sees delayed fixes, paired with the `SENS_GNSS0_DELAY` mismatch (confirm the EKF2 param name first). Plus an IMU-noise scale hook (b) for SDF `<noise>` if x[1,5] must cover wideband noise, not only the rotor vibration.
3. Seeded telemetry-drop (e): expose a per-run seed for the `GZMixingInterfaceESC` generator (currently fixed at `hpp:131`), and confirm the timed `erpm_loss` driver in `run_scenario.py` (UNVERIFIED) and the frozen-duration control.

## Unverified

- Whether `failure_injection` `Delayed` / `Stuck` apply to ESC or GNSS with a duration (only the Stuck call sites were seen).
- Whether `EKF2_GPS_DELAY` exists as an alias of `SENS_GNSS0_DELAY`.
- The `--params` and `sim_params` application loop (`run_scenario.py` around :700).
- `indi_flight/bench/model_variant.py` and `*_params.c` files were not searched.
