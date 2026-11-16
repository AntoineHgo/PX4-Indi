# Route check 45 (sonnet, 2026-11-16, session 45)
Read: STATE, DECISIONS, ANOMALIES A-21..A-23, JOURNAL tail (ledger rows and S40-S44 lines only; no entry text was
read in full), route_check_40, a23_test/README. No source, no logs, nothing flown. Numbers are the ones STATE records.

## 1. Still on the shortest path? Shortest path to a first valid G2 table
Partly. Fixing the vehicle (A-23) is on the path; A-21/A-22 (S40-S44) were not: 5 sessions of margin and G1-gap work on a
plant in a limit cycle, all void. Gates passed: 0 (STATE). route_check_40 item 2 already said "margins of unfixed code are
method validation only" and that defaults must change (PM 42.7 < 45 at defaults); S41-S43 flew on anyway.
Shortest path, in order, each step gating the next:
 a. A clean INDI hover: pitch-rate RMS < 0.02 rad/s, motors < 0.005 on < 1 %, torque_setpoint_achieved > 90 %
    (criteria of the A-23 note; the PSD peak/median criterion is dropped). Now: T94 (derived G1_Y) is the test of the yaw lead.
 b. Defaults from derivation, not from the old fits: G1 R/P/Y from sdf inertia, CA_* geometry, CT/KM and hover thrust
    (decision 4 + stage-4 item 3), as a script that writes the params; plus ACT_TC from one rotor step (A-21 test (3)).
 c. One roll M3a margins set at 800 Hz on that vehicle, model with the attitude P loop (A-21 finding), one seed, 2 periods,
    pre-test checklist including (a). Compare with the model; that is the first valid G2 row. Then pitch/yaw, 400 and 267 Hz.
Not on the path now: A-22 follow-ups, any G1 regression/ridge work (void), the "esc leads command by 15 ms" hunt unless
(a) fails with derived G1_Y, M3b store points, extra second keys on margin equations, outer-break notes before (c).

## 2. Which recorded decision is this a consequence of?
 - Mainly the order "stage 2 before stages 3/4" (MISSION order of work; route_check_40 section 2 named it "the third cause"),
   combined with DECISIONS "Orchestrator decisions" items 3 and 4 (identification concept, airframe-independent defaults):
   still listed "to be written before code", never written. The defaults MC_INDI_G1_R 320 / G1_P 210 / G1_Y 30 are therefore
   unsourced guesses, 5-8x below the plant (violates "Identified, never tuned" and F-3's short justified requirements list).
 - Second: D-G2-INJ's pre-test (u = c + d, fault, landed, generator timing: STATE S39/S40) checked the injection pipeline
   but not whether the vehicle flew cleanly; "Lessons proposed" S44 says so. O-13 ("flown once with the reference controller
   before it enters a validation set") was met by PID only, never by the INDI path.
 - Third: the 2-session-per-anomaly rule (lessons, route check 22) was not applied to A-21/A-22 (S40-S44) because each
   session had a new numerical lead (G1 ridge, 878 analytic, 340 chain); a limit-cycle check on the log would have closed
   it in S40. F-1 (no PID fallback) is not a cause; it only removes the escape route, correctly.

## 3. Fresh start on stage 2
Yes: stage 2 margins should wait for a clean hover with derived defaults. A fresh start would: (1) derive G1 and ACT_TC first
(decision 4 written, one script), (2) make "clean hover" a numeric pre-test gate in the runner before any injection or
second key, (3) put the injection plumbing in the same stage-3 edit as the landed/timeout fixes so one set of margins is
measured on code that stays, (4) take D-G2-BREAK/D-G2-INJ unchanged (their logic holds: u = c + d exact, fault/landed asserted),
(5) apply the 2-session rule to A-21..A-23 and treat any margin that disagrees with the model by > 10 deg as "check the vehicle
first". Keep: estimator, models, unit tests (S37-S40), the M3a firmware; they are valid, only the numbers are void.

## 4. Next 3 sessions (about $3 each, one agent task each)
S46 (sonnet, <= 15 calls): `bench/derive_g1.py` (G1 R/P/Y from sdf + CA_* + hover thrust, writes a .params file; reuses
  the S45 yaw derivation 0.5545 Nm / Izz and the roll 1756 / pitch 1599 formulas) and fly one INDI hover with all three;
  add the clean-hover check (a) to `bench/limit_cycle_check_s44.py` as exit status. Done when: PASS, or motor spectrum +
  u_cmd vs u_meas saved for the chatter. Haiku second key only if time (separate, ~$0.1).
  If T94 (yaw) already clears pin < 1 %, this is a 1-flight confirmation; if chatter remains, the 2-session rule for A-23
  ends here: write the park bound and open the next-mechanism list (telemetry delay/blend, rate limit, ACT_TC, filter).
S47 (sonnet): ACT_TC: motor step in sim (separates tau and latency, STATE S44 plan item (c)), derive the default, set by
  formula in `derive_g1.py`; re-fly the hover, re-check (a). Fix `margins_models.py` for the attitude P loop (A-21 T85).
  Fallback if S46 is not clean: S47 is the chatter mechanism task, not margins.
S48 (sonnet + shell flights, host bash is $0): roll M3a at 800 Hz, measured and model-only, seed 1 and 2, on the clean vehicle;
  report PM/GM/DM against the corrected model; then pitch and yaw in the same session if wall time allows. Result:
  `results/stage2_s48/` first valid G2 row (roll 800 Hz); G2 matrix (3 axes x 3 rates) ~S49-S50. Tell the owner at S48
  that the 5 void sessions are a process cost and ask for Q2-Q4 answers so G1 can be marked passed.
