# A-14 reference altitude, why the staged fix had no effect (session 29)

Read-only investigation. Nothing under `indi_project/` or `src/` was modified and no flights were run.
Docker queries were blocked by the project host guard (`indi_flight/guard.sh`) and were not retried.
Public gz source was fetched to `/home/ahugo/.cache/_aps8.cc` (AirPressureSensor.cc, gz-sensors8 branch) and to the
session scratchpad (`systems_Sensors.cc`, `AirPressureSensor.hh`, `sdf_air_pressure.sdf`).

## Q1. Which SDF is loaded at run time

- `indi_flight/bench/run_scenario.py:31` sets `MODELS_DIR = indi_flight/sim/models`. Lines 173-174 point
  `PX4_GZ_MODELS` and `GZ_SIM_RESOURCE_PATH` at it, for non-x500 models (quad5in).
- `indi_flight/results/a14_close_s28/pretest/gz.log` lines 1-4 cite
  `indi_flight/sim/models/quad5in_base/model.sdf` at L133 (air_pressure gz_frame_id), L151 (magnetometer), L176 (imu), L228 (navsat).
  Those line numbers match the STAGED file (133, 151, 176, 228). The live file has 133, 147, 172, 224.
  So the pretest DID load the staged file with `<reference_altitude>`.
- The live file was reverted after the pretest. `indi_flight/sim/models/quad5in_base/model.sdf` has mtime 04:13:05,
  the installer ran at 04:11:55 (`results/a14_close_s28/status.txt`), and the live file now has no `reference_altitude`.
  Who reverted it is unknown. It was not me.
- `quad5in/model.sdf:4-5` is `<include merge='true'><uri>model://quad5in_base</uri>`. Grep finds no `air_pressure`
  element in `quad5in/model.sdf`, so the base file's sensor is the only definition.
- No copies of `quad5in` model.sdf exist under `build/` or `Tools/simulation/gz/` (find, empty).
- UNVERIFIED: copies inside the Docker image (blocked).

## Q2. Placement of `<reference_altitude>`

- `indi_flight/sim/staged/quad5in_base_model_a14.sdf:132` `<sensor name="air_pressure_sensor" type="air_pressure">`
  > `:136` `<air_pressure>` > `:140` `<reference_altitude>488</reference_altitude>` (before `<pressure>` at :142).
- SDF spec (gazebosim/sdformat `sdf/1.9/air_pressure.sdf`): `air_pressure` > `reference_altitude` (double, default 0.0).
  The path is correct.
- The element is still ignored. gz-sensors8 `src/AirPressureSensor.cc` `Load(const sdf::Sensor&)` (lines 94-139)
  reads only `PressureNoise()`. It never reads `ReferenceAltitude()`. `referenceAltitude` (line 70) is set only by
  the public setter `SetReferenceAltitude()` (line 213, declared in `include/gz/sensors/AirPressureSensor.hh:77`).
- gz-sim8 `src/systems/sensors/Sensors.cc` has zero matches for `ReferenceAltitude` or `AirPressure`. Nothing in gz-sim's
  sensors system calls the setter, so the SDF value never reaches the sensor.

## Q3. gz-sensors version and pressure formula

- Image gz version: UNVERIFIED (docker blocked). `indi_project/docker/Dockerfile:14` says "Gazebo Harmonic".
  Harmonic = gz-sim8 / gz-sensors8. The repo's macOS Harmonic pixi lock (`Tools/setup/macos/pixi.lock:109-113`)
  pins gz-sensors8 8.2.2 and gz-sim8 8.10.0.
- Source checked: gz-sensors8 branch `src/AirPressureSensor.cc` (HTTP 200) and gz-sim8 `systems/sensors/Sensors.cc`.
- `Update()` line 169: `height = referenceAltitude + Pose().Pos().Z()`. Constants at lines 40-52 give the ISA
  formula. `kAirConstantDimensionless` is negative (`/ (-kTempLapse)`).
- The world's `<spherical_coordinates><elevation>488` (`indi_flight/sim/worlds/default.sdf:86-92`) is NOT used by the
  sensor. `Pose()` is the local world Z (about 0 on the ground). Pressure therefore reads sea level whatever the world
  elevation is, which matches 101324 Pa.
- Computed with the same formula (python, k=5.2559, geopotential height): P(488 m) = 95598.7 Pa, P(0) = 101325 Pa.

## Q4. PX4 gz_bridge: gz pressure or its own?

- `src/modules/simulation/gz_bridge/GZBridge.cpp:399/402`: topic `air_pressure_sensor/air_pressure`.
- `GZBridge.cpp:569-580` `airPressureCallback`: `_px4_baro[i].update(now, msg.pressure())` (line 579). The gz pressure is
  passed through. The only other input is a static temperature (line 578). No altitude is computed in the bridge.
- Altitude is computed later in `src/modules/sensors/vehicle_air_data/VehicleAirData.cpp`:
  - :212-214 `pressure_sealevel_pa = SENS_BARO_QNH * 100`, then `getAltitudeFromPressure(...)`.
  - :273-275 `SENS_BARO_AUTOCAL` runs `BaroGNSSAltitudeOffset()` (defined at :521-590). It solves a pressure offset
    (`mid`) so the calibrated altitude equals GNSS MSL altitude.
  - The pretest `pretest_check.md` shows CAL_OFF 5727.5 Pa = 101324 - 95596. So the autocal moves the EKF-side pressure
    to about 95600 Pa. That explains the earlier unexplained 101320 (sensor_baro) vs 95600 (vehicle_air_data) mismatch
    in `design/a14_cause_s27.md`.

## Q5. Conclusion

1. Most likely cause: gz-sim8 / gz-sensors8 never read `<reference_altitude>` from SDF. The fix was loaded (Q1)
   and the element is valid (Q2), but nothing applies it (Q3). The pretest's 101324 Pa is therefore the expected
   output, not a load failure. Consequence: no SDF-only fix exists for Harmonic. A gz system plugin calling
   `SetReferenceAltitude` would be needed, and that is out of tree.
2. Options for a sim baro that reads about 95600 Pa at 488 m:
   - A (raw pressure, smallest code change, SITL only, needs `src/` edit, not made here): in
     `GZBridge::airPressureCallback` (line 579), scale `msg.pressure()` by `P_ISA(H_ref)/P_ISA(0) = 0.94349` with
     `H_ref` = 488 from a parameter. Scaling is multiplicative, so the vertical gradient is 11.33 Pa/m vs the true
     11.46 Pa/m at 488 m (about 1%).
   - B (params only, no src, no model): `SENS_BARO_AUTOCAL 0` and `SENS_BARO_QNH` = 1073.94 hPa. Raw stays 101324 Pa, but
     the altitude from `getAltitudeFromPressure` reads 488 m at ground. Gradient implied by QNH is 12.15 Pa/m vs true
     11.46, so the altitude scale is about 6% too small (about 0.3 m at 5 m hover). Does not give the raw 95600 reading.
   - C (existing candidate, `design/a14_cause_s27.md`): `EKF2_BARO_CTRL 0` (GNSS height only, baro not fused). Does not
     change the raw reading. It is the cleanest bench option if the test only needs the EKF to ignore the sim baro.
3. Recommendation: option C for the A-14 closing test (no code change). Option A if a physically consistent sim baro is
   needed later. Option B is not recommended (6% scale error).

## Unverified / open
- Image gz and sdformat versions and the image's own model copies (docker blocked by the project guard).
- Only `systems/sensors/Sensors.cc` of gz-sim8 was checked for a setter call. Other gz-sim files were not.
- Whether the `<data-string>` spawn (gz.log lines 5-8) carries the reference element.
- PX4 `getAltitudeFromPressure` formula (assumed ISA with T0 = 288.15) and the `SENS_BARO_QNH` valid range. Not read.
- Full `BaroGNSSAltitudeOffset` logic (only the signature region was read).
- Who reverted the live model file at 04:13:05.
- Option A is a suggestion only. No code was changed, and no simulation was run.
