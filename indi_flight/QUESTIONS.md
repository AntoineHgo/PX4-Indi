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

## Q31 (S213, 2026-11-23): G3 halted on an INDI loss of control at corner C3. BLOCKING for G3 and G6
Question: after the second G3 NOT PASSED, which route do we take?
Context:
- Chain C212 (ACT_TC drawn in the S211 box) halted at run 024, draw 264, corner C3: thrust scale 0.351 on all motors,
  motor 3 further x0.709 (ceiling 0.249), mass x1.3. INDI tilts past 60 deg at 60.8 s (speed 4) and 61.0 s (speed 1).
  The same plant at freeze-10 (ACT_TC 0.033) lost control at the same time: identifying ACT_TC did not change it.
  PID flies the draw (tilt max 40 deg). Verdict written: GATES "G3 verdict, re-fly ... (S213)".
- Mechanism on the S199 logs (`results/g3_refly_s199/CAUSE_S199.md`): at the fault both stacks spin up in yaw (weak CW
  rotors). PID recovers roll/pitch, but INDI's pitch rate runs against its setpoint and every rate setpoint reaches the
  220 dps limit. Motor 3 saturates only after the tilt is lost. Shown on the log: yaw first, then INDI fails to recover.
  Inferred, not tested: why INDI fails to recover (no roll/pitch-over-yaw priority in the increment, or the measured
  torque gap from the unknown weak motor).
- The GATES failure-explanation rule (restore drawn factors one at a time) has not been run on 264.
Options:
- A. Stop G3 here. G3 is NOT PASSED, and the C3 corner (saturation plus weak motor) is a stated limit in G8. G6 item 7
  and G7/G8 go ahead on freeze-10, and G6 is reported as not passable because it requires G3.
- B. (recommended) One session of factor restoration on 264 (data only, about 10 speed-1 flights). Then, only if a fix
  probe removes the loss of control on the log, one firmware fix (freeze discipline). The rows it invalidates are
  named and re-flown (G2/G4/G5 subsets), then the G3 campaign restarts critical first. If the restoration shows
  beyond-range physics (class b), the result comes back to you.
- C. Re-open the outer/inner-loop saturation design (yaw priority in the INDI increment) as a design step before any
  probe. That costs more sessions.
Meanwhile: nothing flies. G8 drafting continues (not decided by Q30/Q31); G6 item 7 waits. Q30 stays open for the next campaign.
Blocked: G3, G6. Not blocked: G8 drafting, G7 items that do not touch firmware.
