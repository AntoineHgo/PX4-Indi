# Route check 79 (S79 start, 2026-11-18)
Read: STATE, DECISIONS headings (D-GAP, D-RATE-BLD, D-RATE-BLD-EDGE, D-G2-BREAK by title and STATE summary), ANOMALIES A-34/A-35 rows,
JOURNAL tail, route_check_74. No code or results opened, nothing flown. Gates still 0/8 passed after 78 sessions.

## 1) Still on the shortest path?
Mostly the rate-blend work (S75-S77) was on path; the A-34/A-35 work (S77 trace, S78 model) was a detour and broke the route-check-74 rule.
- ON PATH: D-RATE-BLD-EDGE (S75), rate M3a at 800 and 400 Hz (S76, S77: PM 68-70 deg, GM 13-16 dB, DM 43-51 ms, all inside G2 limits
  GM>=6, PM>=45, DM>=2 periods+latency), 69/69 unit tests. These are G2 rate-loop evidence and satisfy D-RATE-BLD precondition 1-3.
- DETOUR: A-34 (PM 69 vs 77 deg, f_c 4.1 vs 3.1 Hz) is a drift between two PASSING measurements. No gate test failed; rule 74 said
  "no new anomaly chase unless a gate test fails, one session each". A-34 took S76-S78 (3 sessions) and spawned A-35 (model offset
  0.2-1.7 dB / 17 deg at 1 Hz), which only affects the linear-model cross-check, not the measured G2 margin. The fly-da64bc26b3^ worktree
  test and the A-35 hunt must NOT run before the G2 freeze; park both as "explained enough: setpoint lead (D-RATE-LEAD) moves PM, model
  reproduces within 1.3 deg / 0.07 Hz".
- STALE on the NEXT list: (e) combined opus review and (d) runner RC/manual stub were pushed back again; the D-RATE-BLD firmware default
  (rule 74: "do not wait for the full margin table") is STILL not committed although its preconditions are now met.

## 2) Which decision is the difficulty a consequence of?
Decision 2 (measured actuator state fed back, no PID fallback), as in route check 74, now through a second face: measured margins are
taken on a loop whose behaviour depends on three coupled knobs (setpoint lead D-RATE-LEAD, blend D-RATE-BLD, ACT_TC). Every param change
shifts PM by several degrees, and the analytic model (margins_models.py, D-G2-BREAK cross-check) must be re-fitted each time. The real
mistake is process: the model was treated as a second gate (bins within 1 dB/5 deg) instead of a cross-check; D-G2-BREAK makes the
MEASURED torque-setpoint break the gate.

## 3) Fresh start on this stage
- Freeze the inner-loop defaults (lead, ACT_TC, blend 1.0) once, then take the G2 table once per rate (400, 800) from a single param file,
  and tag the commit. Margin model tolerance = "same sign and < 10 deg" until G2 passes; refine afterwards if the report needs it.
- Make "gate fails" the only trigger to open an anomaly row; drift between passing runs goes in one line in the G2 table notes.
- Build the outer-loop injector (D-G2-INJ analogue) at the same time as the rate injector, so G2 is one campaign, not two.
- Fix the flight matrix for G3/G5 before stage 3 closes, so defects show up in the matrix, not one scenario at a time.

## 4) Next 3 actions (small budgets, ~$1.4 per session)
1. (no agent, ~$0.4) Set firmware default MC_INDI_ACT_BLD 1.0 in its own commit (use `commit` skill, `git commit -F` file), rerun the
   existing unit tests (69/69 plus weak-motor), update STATE and D-RATE-BLD to ACCEPTED. Park A-34/A-35 as PARKED with the one-line
   reason above (rule 74 applies). Delete the A-34 flight and A-35 from NEXT.
2. (one sonnet task, ~$0.9; brief at cap >= $2) D-GAP outer-loop injector at the accel/collective setpoint in mc_indi_pos_control
   (MC_INDI_POS_INJ_*, log c/d/u, mirroring D-G2-INJ) plus csv script; flights and haiku second key go in a following session.
   This is the only item that unblocks the outer-loop G2 numbers.
3. (no agent for the stub itself if small, else sonnet ~$0.9) runner RC/manual stick-path stub and PVA slice (ZSINE_O6): the long pole for
   G5 and G3 scenario coverage; do it before land/re-take-off and before the combined opus review (e).
Rule for S80+: stage-3 time box is spent; any new inner-loop item needs a failing gate test first.
