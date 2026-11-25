# Questions to the owner

No open question (S50). Q1-Q4 closed, archived in JOURNAL.md.

N1 closed S61 (moved to JOURNAL.md; open items C2, C3 carried in STATE.md).

N2 closed S69 (summary in JOURNAL.md).

Q5 closed S70 (no owner objection to addendum 6; summary in JOURNAL.md).

Q6 closed S120 (owner answer B, conditions (i)-(v) in DECISIONS.md D-IDENT; full text in JOURNAL.md).

Owner directive 2026-11-20 (F-7/F-8/F-9) closed S134: acted on (DECISIONS D-F7-GROUND, GATES 5b, STATE
next actions); text in JOURNAL.md.

Q7 closed S140 (owner answer A: G5.7 validity at the 4 edges leaving posctl; written into GATES 5b; text in JOURNAL.md).

Q8-Q15 and the owner note of 2026-11-21 closed S175 (answers acted on: GATES.md "Owner amendments S175",
DECISIONS D-OWNER-Q8-Q15 and D-JFF-KEEP; full text in JOURNAL.md S175).

Q16 closed S178 (owner answer A: G2 PASSED once the freeze-7 outer cells and 2 rate/att spot-check cells pass;
3 rate x-check groups reported as evidence limit, A-51 open; full text in JOURNAL.md S178).

Q17 and Q18 closed S180 (owner answers A; GATES "Owner amendments S180", D-OWNER-Q17-Q18; text in JOURNAL.md).

## Owner note (2026-11-21, after Q17): stay inside INDI scope
1. Scope line. A behaviour that the PID reference shows too (same scenario and seed, same signature in the gate
   metric) is a PX4 fact, not INDI work: report both stacks' values and, if it blocks a gate row, write the owner
   question. Do not chase or fix stock PX4 code (EKF2, mc_pos_control, land detector, commander) or simulator
   plumbing beyond the injectors that the gate factor tables require. No new hook without a gate row that consumes it.
2. G3 tel_frozen hook. Keep it, since the G3 factor table and C5 list frozen telemetry, but build the simplest injector
   (one session, two keys). If it does not fly after that session, stop and write an owner question proposing to drop
   the frozen factor from G3 instead of continuing the plumbing.
3. G4 chatter keys. Before any F2 firmware work, reconcile key 1 (88.5 Hz) and key 2 (33.5 Hz) on the same
   cruise_typ_s1 lemniscate window (results/g55_gain_probe_s179). F2 targets only a line that both keys agree on.
   One sonnet task, existing scripts.
4. G4 item 3 in the XY_P 1.2 probe (altitude_mean 0.29 m, limit 0.1). Look up the freeze-7 value and fly the PID
   reference before any cause search (point 1 applies).

S180: points 3 and 4 acted on (results/g55_gain_probe_s179/RECONCILE_S180.md: keys agree on 33.5 and 89.25 Hz;
cruise item 3 offset equals PID, not a G4 row). Points 1-2 stand as rules (point 2 in STATE next action 4).

Q19 closed S183 (owner answer A with PID guard; GATES "Owner amendment S183", D-OWNER-Q19; text in JOURNAL.md S183).

Q20, Q21, Q22 closed S187 (owner answers acted on: GATES "Owner amendments S187", DECISIONS D-OWNER-Q20-Q22; full
text in JOURNAL.md S187).

Q23 closed S191 (owner answer B: full revert of aa4fd2654a, D-JFF-KEEP overturned for it; DECISIONS
D-OWNER-Q23; full text in JOURNAL.md S191).

Q24 and Q25 closed S197 (owner answers B and B: GATES "Owner amendments S197", D-OWNER-Q24, D-OWNER-Q25,
design/airframe_requirements.md; full text in JOURNAL.md S197).

Q26 closed S207 (owner answer: check first, C not chosen; items 1-4 done, results and recommendation in Q27;
full text in JOURNAL.md S207).

Q27 closed S208 (owner answer: identify ACT_TC first, no box change now; acted on in GATES "Owner amendments S208",
DECISIONS D-OWNER-Q27; full text in JOURNAL.md S208).

Q28 closed S211 (owner answer A, box r [0.88, 1.02] x tau_mean; GATES "Owner amendment S211", DECISIONS
D-OWNER-Q28; full text in JOURNAL.md S211).

Q29 closed S211 (owner answer A + both cuts: G3 300 fail-fast, G6 item 7 corners only; GATES "Owner amendment
S211b", DECISIONS D-OWNER-Q29; full text in JOURNAL.md S211).

Q30 closed S214 (owner answer B with review changes; GATES "Owner amendment S214", DECISIONS D-OWNER-Q30;
full text in JOURNAL.md S214).

Q31 closed S218 (owner answer B + escalation route, binary 903eae63; GATES "Owner amendment S218", DECISIONS
D-OWNER-Q31; full text in JOURNAL.md S218).

Q32 closed S226 (owner answer A bounded + item 2 sub-question yes; GATES "Owner amendment S225", DECISIONS
D-OWNER-Q32; full text in JOURNAL.md S226).

## Q33 (S227, 2026-11-25): G3 item 5 on the new g3_lemniscate scenario fails for PID too. BLOCKING for G3 item 5.
Context: GATES item 5: "after each injected event (gust, fault start) back within 0.3 m and 3 deg of the pre-event
reference in <= 5 s and no re-excursion > 0.3 m for 5 s". With the S214 events at the start of the main lemniscate
there is no static pre-event point, so both keys use the commanded path at the same time (D-G3-KEYS-S227, the
literal and stricter reading). Then ordinary tracking error counts against 0.3 m, which is tighter than item 4
(0.5 m horizontal RMS). Pre-test (results/g3_pretest_s227, seed-173 draw 0, binary 903eae63, both keys agree):
INDI items 1-4, 6 pass, item 5 FAIL 0.576 m; PID reference same draw: item 5 FAIL 1.210 m, item 4 FAIL 0.764 m.
Options:
A (recommended) item 5 measures what the event adds: deviation from the commanded path minus the pre-event
  tracking error (e.g. 0.3 m above the 95th percentile of the 5 s before the event), threshold unchanged.
B item 5 events in a hover segment before the lemniscate (static pre-event reference), as the text reads; scenario
  change, both keys follow.
C keep as is: item 5 then binds on lemniscate tracking and fails for both stacks.
Meanwhile: no re-fly, re-score or note on item 5. Next session flies the (b) FREEZE-10 baselines 262/283 on the new
scenarios scored on items 1-4 and 6 (no open question decides those). Not blocked overall.

Answer:
B with amendments (owner, 2026-11-25, with an independent review agent's second opinion). Gate text: GATES "Owner
amendment Q33". Findings behind it (checked on results/g3_pretest_s227, both keys, both stacks): the only scored event
is the main-segment start, return time ~0 s, so 0.576 m (INDI) / 1.210 m (PID) is lemniscate tracking error, not event
response; the gust (fixed gust_x timing: 2 s ramp, 10 s steady, 1 s gust, peak at +12 s) is scored by neither key and
not skipped by item 2; A as written fails (its pre-event 5 s is the settle hover).
1. Scenario: settle -> event hover -> main segment (lemniscate / stick) -> 35 s hold. Events in the event hover on a
   static reference: fault step and wind ramp at t0, gust at t0 + 12 s. Event hover length >= gust end + 10 s
   (5 s return + 5 s quiet), derived in code from the disturbance.py profile constants (23 s today), not a literal.
2. Both keys: item 5 events = fault start (t0) and gust (t0 + 12 s); item 2 skip windows (S225) get the gust time too.
   Self-tests in both keys for the gust event and its skip, break-checked.
3. Item 5 reference per mode: position = hover setpoint (trajectory_setpoint); attitude = q_d (level, zero sticks);
   rate = not applicable (items 1, 2, 6 cover rate runs). Thresholds unchanged (0.3 m, 3 deg, 5 s, 5 s).
4. The wind ramp is a disturbance, not a scored event (text names gust and fault start). The sag keeps its slow ramp
   from the scenario start and is not an event; each run tables where its ramp ends relative to t0.
5. Item 4 window = main segment only (fault and steady wind already on). Limits unchanged.
6. Same pattern in g3_stick_zsine; check the q_d reference exists before t0.
7. Order: build (1-2, 6) -> re-fly the S227 pre-test draw 0 for INDI and PID on the new scenario, both keys -> then the
   FREEZE-10 baselines 262/283 on the new scenario. S227 pre-test results stay evidence for items 1-3, 6 only. If PID
   fails item 5 again on the new scenario: new owner question, no silent change.
Cost accepted: ~+23 s per run (~1.9 h per 300 runs at speed 1).
