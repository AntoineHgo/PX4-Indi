# Airframe requirements for the INDI stack (F-3) and bring-up items

One page. Each requirement names why it is needed and where it is recorded; the G8 report and the `docs/en` page
take their list from here.

| # | requirement | reason | record |
|---|---|---|---|
| R1 | Rotor-speed telemetry (bidirectional DShot eRPM) on every motor; without it INDI refuses to arm | measured actuator state (O-5) and identification | design/ident_concept.md l.42 |
| R2 | Rotor geometry in `CA_*` (positions, spin directions, thrust and moment coefficients) | measured torque built with the control-allocation library | module source, D-IDENT |
| R3 | Both INDI modules start in place of the stock ones before first arm | one controller from arming to disarming (F-7) | DECISIONS l.828 |
| R4 | EKF2/SENS GNSS delay (`SENS_GNSS0_DELAY`) within 50 ms of the measured GNSS latency | outer loop less tolerant of a stale position than PID beyond about +60 ms (G3 draws 02/05, S192 probe) | GATES "Owner amendments S197", D-OWNER-Q24 |

Bring-up checklist items collected so far (bench, before the first flight):
- Telemetry rate and latency per motor; frozen-value behaviour of the DShot driver (G8 text).
- Loop timing of rate and position modules at the configured rates (G8 text).
- Check both INDI modules run before first arm (R3).
- Measure the GNSS latency of the receiver and set `SENS_GNSS0_DELAY` within 50 ms of it (R4).
