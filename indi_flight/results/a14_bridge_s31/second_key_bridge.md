# Second-key review: 4443079c0b (gz_bridge baro at world elevation, A-14)

Scope: read-only review of `git show 4443079c0b` and `indi_flight/bench/tests/test_baro_elev.py`. No build, no simulation. The only pure-math runs were a standalone Python check of the ISA numbers and the existing test file.

## Verdict: AGREE-WITH-ISSUES

The ISA mapping is correct and the units are consistent (Pa in, Pa out). The approach fixes the 488 m step. Three items need follow-up: a likely double count of the spawn height in the reference altitude, a data race on the reference state, and a wrong expected constant in the test.

## Findings

1. **ISA formula and units: correct (AGREE).**
   - Constants at `src/modules/simulation/gz_bridge/GZBridge.cpp:571-574`: `ISA_P0 = 101325` Pa, `ISA_T0 = 288.15` K, `ISA_LAPSE = 0.0065` K/m, `ISA_EXPONENT = 9.80665*0.0289644/(8.31432*0.0065)`.
   - Inverse at `GZBridge.cpp:591`: `h = (T0/L)(1 - (p/P0)^(1/K))`. Forward at `GZBridge.cpp:592`: `p = P0 (1 - L(h + alt_ref)/T0)^K`. Both are the standard troposphere relations, and the sign is right (positive `alt_ref` lowers the pressure).
   - Numeric check (standalone Python, same constants): K = 5.255876, p(488 m) = 95598.3 Pa, dp/dz at ground = -12.013 Pa/m, dp/dz at 488 m = -11.460 Pa/m, noise gain = 0.9540.
   - Units: `msg.pressure()` is Pa (gz `FluidPressure`), and the `PX4Barometer::update(timestamp, float pressure)` signature at `src/lib/drivers/barometer/PX4Barometer.hpp:55` takes Pa. The pre-existing code also passed Pa directly. No hPa/mbar mix-up, and no sign error.
   - Nit: the code uses R = 8.31432, not the 8.31446 in the review brief. With 8.31446, K = 5.255788 and p changes by about 0.1 Pa. Negligible, but the constant should be stated consistently. The comment at `GZBridge.cpp:569` ("as used by gz-sensors") is unverified here, because gz-sensors source is not in the repo.

2. **World elevation source: the first navsat altitude includes the spawn height z0 (CONFIRM, with caveat).**
   - `navSatCallback` at `GZBridge.cpp:911-913` sets `_alt_ref = msg.altitude()` on the first message. That is the sensor's MSL altitude, which in gz-sim's navsat model is world elevation plus the sensor's local z, so it includes spawn z0.
   - The baro remap at `GZBridge.cpp:591-592` uses `h_local` from the gz pressure, which is the vehicle's local z, and that also includes z0. The result is `alt = z0 + (488 + z0)`, so z0 is counted twice in the altitude that the baro is mapped to.
   - Error: about 11.46 Pa per metre of z0 (the sign follows the lapse, so the mapped pressure is slightly low). For z0 = 0.1 / 0.2 / 0.5 m that is about 1.1 / 2.3 / 5.7 Pa, or about 0.1 / 0.2 / 0.5 m of altitude bias.
   - Caveat: I did not read the spawn pose (a zsh glob failed) and the gz-sim NavSat semantics are not in the repo. The double count is inferred from the code and should be checked against the spawn height used by the SITL launch. The correct fix is to set `_alt_ref` to the world elevation (488 m from `Tools/simulation/gz/worlds/default.sdf:91`), or to subtract the first-sample local z.
   - Side effect: `GZBridge.cpp:759` publishes `ref_alt = _alt_ref` in `local_position_groundtruth`. That was already the navsat altitude before this commit, so the ground-truth reference altitude carries the same z0 offset. It is a pre-existing bug that this change now also feeds into the baro.
   - Impact: the bias is constant from the first sample, so SENS_BARO_AUTOCAL plus GPS fusion should largely absorb it in relative height. It still affects absolute altitude and ground-truth comparisons.

3. **Ordering with existing noise and temperature handling, and the step question.**
   - Noise: the 3 Pa gaussian pressure noise is added by gz-sensors in `Tools/simulation/gz/models/x500_base/model.sdf:225-229`, before the bridge. The remap therefore carries the noise through with gain 0.954, which is the intended behaviour. The bridge has no other baro noise path, so nothing is applied twice.
   - Temperature: `set_temperature` at `GZBridge.cpp:598` runs after the remap and does not feed the pressure. `_temperature` is set from the gz temperature at `GZBridge.cpp:617`, so there is no ordering conflict.
   - Start-up: with GPS enabled, samples before the first fix hit `GZBridge.cpp:594-595` and return without publishing. So no sea-level sample is published before the reference, and the mapping itself causes no step. The first published sample is already remapped.
   - Race (see 4): a stale or torn read of `_alt_ref` could produce one sea-level sample after `_pos_ref` reads as initialized, which would be a 488 m step.
   - GPS disabled: `_pos_ref` never initializes, so the baro stays at sea level for the whole run. That is consistent but not "at world elevation", and it contradicts the commit message. Confirm this is intended.
   - Not read: `GZBridge.cpp:101-110` (what happens when `subscribeNavsat(false)` fails). If it fails silently, the baro is held forever.

4. **Thread safety (medium risk, AGREE-WITH-ISSUES).**
   - `airPressureCallback` (`GZBridge.cpp:590`) and `navSatCallback` (`GZBridge.cpp:911-913`) are registered on separate gz subscriptions (`GZBridge.cpp:392-408` and `428-444`), so they can run on different transport threads.
   - `_alt_ref` (`GZBridge.hpp:207`) and `_pos_ref` (`GZBridge.hpp:206`) are plain members with no mutex or atomic. The comment "set before the init flag" relies on store ordering that the C++ memory model does not guarantee.
   - Fix: guard both with a mutex, or use `std::atomic<bool>` with release/acquire ordering for the init flag.

5. **Test accuracy (test_baro_elev.py).**
   - Passes: `python3 -I indi_flight/bench/tests/test_baro_elev.py` exits 0 and prints `P(0m,488m)=95598.3 Pa dP/dz=-11.46 Pa/m noise gain=0.954`.
   - Wrong expected value: line 41 asserts the noise gain is 0.944 with tolerance 0.01. The true gain is 0.954, so the check passes only because the difference is just under the tolerance. The expected constant should be 0.954 and the comment on line 39 updated.
   - The derivative check at line 38 (-11.3 ± 0.3) is loose, and the true value -11.46 sits inside it. It is acceptable, but it would not catch a z0 double count, since that changes `alt_ref` rather than the mapping.
   - The test mirrors the formula only. It does not cover `navSatCallback`, the z0 issue, or the thread safety, so it does not verify the bridge itself.

## Suggested follow-ups (not applied)
- Set `_alt_ref` from the world elevation, or subtract the first-sample local z, and re-check the ground-truth `ref_alt` at `GZBridge.cpp:759`.
- Add synchronization for `_pos_ref` and `_alt_ref`.
- Correct the test expectation at line 41 to 0.954.
- Check `GZBridge.cpp:101-110` and the spawn height used by the SITL launch.
