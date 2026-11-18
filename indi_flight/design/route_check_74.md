# Route check 74 (sonnet, S74 start, 2026-11-18)
Read: STATE, ANOMALIES (first 60 lines, truncated rows), DECISIONS headings + D-GAP + D-RATE-BLD, JOURNAL tail 10, route_check_69. No code or results read, nothing flown.

## 1) Is NEXT S74 on the shortest path?
Partly. 0/8 gates passed after 73 sessions. Route check 69 asked for slice 2 + G3-G8 first tests; S70-S73 delivered the thrust-gap
slice (D-GAP) and found the rate-blend default. Both were real defects that would have invalidated G3/G5 flights. But the S74 list has
5 items, all inner-loop or outer-loop hygiene; none is a gate test (G3 campaign, G4 noise, G5 modes, G6 procedure).
- KEEP (1, default change): set MC_INDI_ACT_BLD 1.0 as the firmware default now, with the weak-motor unit test (break-checked).
  Cheap, and every later flight then runs the default. Do not wait for the full margin table first.
- MERGE (1) rate-loop M3a margins at tb 1.0/0.3/0.1 with (3) D-GAP margin items (resonance, overshoot, velocity-break PM at tb, tb/3):
  one campaign, one table; same mechanism (complementary blend) in two loops.
- MERGE (1) snap-vs-freeze fix with (4) combined opus review: apply the D-GAP freeze rule to the rate loop, unit test, review once.
- DROP: separate explanation of the stage-1 0.1 s crash (A-1 is PARKED with bound Tb 0.3 s); the tb 0.1 margin is a by-product of
  the merged campaign, not a goal.
- RE-ORDER: (5) PVA mode slice and the runner RC/manual path (none today) are the long pole for G5 and have been pushed back since
  S65. Put them ahead of (2) land/re-take-off, which is a corner of D-GAP, not a gate. Defer (2) until the runner scenario is needed by G3.

## 2) Which decision is the difficulty a consequence of?
Decision 2 (measured actuator state fed back into the INDI law, no PID fallback) with the lesson-9 consequence: measured-state INDI
has no DC integral action, so every loop needs a model/measured blend. The rate-loop blend default was left at 0 (S49-S72) while
D-GAP re-derived the same need in the outer loop (S70-S72). Same root found twice. Second layer: gates were not written as a fixed
flight matrix first, so defects surface one scenario at a time.

## 3) What a fresh start on this stage would do differently
- Open with a "DC-closure checklist": for each loop (rate, collective, yaw, outer) state where integral action comes from, and test
  it on a weak-motor / thrust-scale 0.85 plant before any tuning. Would have caught A-33 and the 0.37 m gap early.
- Fly one fixed scenario matrix (hover, step, gap085, loss08, gust, one mode) on every default change, not 1-2 ad-hoc scenarios.
- Build modes thin and early (runner RC/manual path first), polish margins after.
- One shared blend class with one set of edge rules (freeze, not snap) used by both loops.

## 4) Recommendation, next 2 sessions
S74 (one sonnet ~30 calls + few flights):
 a. Firmware: MC_INDI_ACT_BLD default 1.0 s; rate blend freeze-on-edge (landed/off/telemetry invalid, as D-GAP); weak-motor
    closed-loop unit test failing at tb 0 and with snap (break-checked). Mark D-RATE-BLD ACCEPTED on that evidence.
 b. Re-fly loss08, gap085 and one nominal hover/step at defaults (no override); haiku second key only if cheap.
 Unblocks: every later flight runs the default; G3 pre-tests become valid.
S75:
 a. One merged M3a margin campaign (rate tb 1.0/0.3/0.1, collective tb and tb/3), single table against G2 thresholds. If tb 1.0
    fails, go to option (ii) per D-RATE-BLD.
 b. Runner: RC/manual stick path stub, then the PVA mode slice (ZSINE_O6) if budget remains.
 Defer to S76: combined opus review (after a and b exist, so it reviews once), land/re-take-off flight.
Rule: no new anomaly chases unless a gate test fails; cap any new anomaly at 1 session.

## 5) Escalate to owner?
No item meets the criteria today. Watch: if the S75 margin table shows tb 1.0 failing the G2 thresholds, D-RATE-BLD flips to the
per-motor estimator (option ii), an architecture change: escalate then. Informational: 73 sessions have passed 0 gates; the first
gate that can plausibly pass next is G2 (rate-loop tables at 400/800 Hz).
