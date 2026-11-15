# Outer-loop architecture candidates, round 4 deltas (session 13, 2026-11-15)

Deltas to A (r2 A1-A9, r3 A10-A12) answering `outer_loop_review_r3.md` (no BLOCKING, 4 MAJOR, 4 MINOR). No
interface changes against r3 (same inputs, outputs, edges), so no new full review round: these are implementation
rules, checked by the stage-5 code review and the tests named below.

## A13. One LIB instance, all axes, every cycle (R3-1)
- `IndiAccelControl` runs on all three axes every cycle while the stage is active. On an acceleration-only group
  only its *output* is replaced by the open-loop share (A15). No reset at e7.
- `reset()` stays for the whole-stage edges e1-e6 (A3) only.
- Test: Altitude mode 60 s, z filter states equal those of a run where xy is tracked (filters never reset).

## A14. The LIB starts at a_ref (R3-2)
- Position and velocity loops are stock PositionControl (A9), which already handles NaN axes. The LIB's own
  position/velocity steps are bypassed (gains 0, or entry point at a_ref), so its validity gate needs only a finite
  a_ref on the INDI group(s) and a valid specific-force measurement. NaN p/v on an open group no longer drops the
  stage to bypass.
- Test: Altitude mode with GNSS lost (vxy NaN): z stays INDI; blind descent: z open, xy open, stage active.

## A15. Open-group share and entry transient (R3-3, R3-4)
- Open xy share: stock `body_z` direction scaled by the z group's vertical thrust,
  `thr_xy = body_z_xy / body_z_z * thr_z`, then A4. The stick -> tilt meaning is stock (tilt = atan(a_xy/g)).
- Open -> INDI (e7 entry): the group carries an offset `o = a_f - a_c` frozen at entry, decayed with tau 0.4 s,
  increment rate-limited as a backstop. Entry needs 0.5 s of continuous tracked pattern (dwell); exit to open loop is
  immediate (stock-equivalent edge).
- Tests: Altitude -> Position at 10 m/s, tilt step < 2 deg and collective step < 2 % of hover at the edge;
  vz-validity flapping at 5 Hz, no limit cycle, z stays open until the dwell is met.

## A16. A11 and classifier amendments (R3-5, R3-6, R3-7)
- A11 (b)/(c): integrators frozen, not reset, across e7 and on open groups. The decision-2 test keeps battery sag.
- Classifier input = the setpoint PositionControl accepted after the MPC fallback (MPC:612-627).
- Precedence: the state bypass (A3/A8, ground idle) wins over e7.
- VTOL transition pattern (FTT:88, :105): VTOL is not served (A1); the pattern is still in the classifier unit test.
- e6 gap from the raw timestamp difference, before the dt clamp (MPC:390-391) and the LIB dt check (LIB:206).

## A17. Start without fallback (R3-8)
- Decided by F-1 (`DECISIONS.md` D-start-fallback): rc.mc_apps if/else, no `||`. If an INDI module fails to start
  the vehicle refuses to arm and reports why. The mechanism (with commander at zero diff) is fixed at implementation
  and tested by forcing a start failure.

## Status
All r3 findings answered. Architecture A (A1-A17) goes to the owner for confirmation (QUESTIONS.md, Q1).
