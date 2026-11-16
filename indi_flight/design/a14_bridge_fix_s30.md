# A-14 bridge fix (D-A14), session 30

Sim-only change in `src/modules/simulation/gz_bridge/GZBridge.cpp`. Not built, not run (orchestrator builds in docker).

## Exact change
- `airPressureCallback`: when `_pos_ref.isInitialized()`, compute `h_local` = ISA altitude of `msg.pressure()`
  (P0 101325 Pa, T0 288.15 K, lapse 0.0065 K/m, exponent g*M/(R*L) = 5.2559, same constants as gz-sensors),
  then publish `P = ISA_P(h_local + _alt_ref)` through `_px4_baro[i].update(...)`.
- Added `#include <cmath>` and four `static constexpr double ISA_*` constants before the callback.
- `navsatCallback` (first fix): `_alt_ref = msg.altitude()` is now assigned BEFORE `_pos_ref.initReference(...)`, because the baro
  callback (other gz-transport thread) uses `isInitialized()` as the "reference known" flag. No atomics or fences (same
  unsynchronised style as the existing code).
- Baro temperature left as is (static `_temperature`, line unchanged); it is not computed from altitude.

## Where the elevation comes from
`_alt_ref` = altitude of the first navsat message (raw gz value, GNSS noise is added later in `addGpsNoise`, so `_alt_ref` is
noise free). That is world elevation 488 m plus the vehicle's spawn height z0 at that instant. The bridge does not read the
world spherical coordinates, and subtracting the local z was not cheap. Consequence: the mapped pressure double counts z0
(spawn height, expected well under 1 m, about 11 Pa per metre of z0), a constant offset that the EKF/baro autocal absorbs. Unverified: actual z0.

## Behaviour before the reference is known
- If `SIM_GZ_EN_GPS > 0`: baro is NOT published until the first navsat fix. Publishing sea level and then 95600 Pa would be a
  5.7 kPa step visible to EKF2/autocal after start; holding off removes it. The navsat sensor starts alongside the baro, so
  the delay should be about one navsat period; EKF2 waits for baro data anyway. Unverified in a run.
- If `SIM_GZ_EN_GPS == 0`: no fix will ever come, so pressure is passed through unchanged (old behaviour).

## Checks
`python3 indi_flight/bench/tests/test_baro_elev.py` passes: P(0 m local, 488 m) = 95598.3 Pa; round trips for elevations
0/100/488/2000 m and local 0..300 m; dP/dz at 488 m = -11.46 Pa/m (true ISA; the multiplicative option A of
`a14_refalt_s29.md` would give -11.33); 1 Pa of gz noise maps to 0.954 Pa (ratio of gradients).

## Unverified
- Compile (float/double mixing, `SIM_GZ_EN_GPS` type `.get() > 0`), runtime behaviour, z0 value.
- gz-sensors exact formula is mirrored from the constants/structure in `a14_refalt_s29.md`, not re-fetched.
- Multi-baro: all instances use the same `_alt_ref`.
- With the fix, SENS_BARO_AUTOCAL offset should be near 0 Pa at ground (expected check: CAL_OFF in pretest_check).
