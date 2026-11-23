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

## Q30 (S213, 2026-11-23): G3 item 3 window. BLOCKING for G3 item 3 (not for items 1, 2, 4-6)
Question: which window scores G3 item 3 (steady-state horizontal RMS <= 0.30 m with wind)?
Context:
- GATES (line ~255) defines it as "last 10 s of a hold >= 20 s after the last transient, truth". The scorer
  `bench/g3_score.sh` (header "DEVIATION, stand-in scenarios have no 20 s hold") scores the final 3 s hold segment,
  which starts about 0.5 s after the arrival from the trajectory. This deviation was never written in GATES or
  DECISIONS. It also scored the freeze-10 campaign (15 item-3 misses, then under a 95 % quota).
- Chain C212 run 022 (draw 262, corner C3, thrust 0.351, wind 1.7 m/s) item 3: INDI 0.317 m (speed 4), 0.308 m
  (speed 1, both keys) -> a confirmed miss under the S208 no-quota rule. PID, same draw, speed 1: 0.138 m.
- Decomposition (`results/g3_refly_actc_s212/speed1_s213/ITEM3_DECOMP.md`): mean offset INDI 0.10-0.13 m, PID 0.12 m
  (no steady gap); the excess is INDI settling from 0.6 to 0.15 m in about 2 s inside the window (PID about 0.5 s).
  Over the last 1.5 s of the window: INDI 0.13-0.19 m, PID 0.08 m. Item 3 here measures settling, not steady state.
  Item 5 (recovery <= 5 s) is the row that covers settling.
- Item 2 at speed 1 passes for INDI on run 022 (PID fails item 2 on the same draw), so the halt was not confirmed and
  the chain resumed on 2026-11-23 at 20:10 for items 1 and 2.
Options:
- A. Keep the 3 s window (write the deviation into GATES). Run 022 fails item 3, so G3 is NOT PASSED for this campaign.
- B. (recommended) Apply the written rule: lengthen the final hold of the G3 scenarios to >= 20 s, score its last
  10 s. Only the scenario timing changes, no threshold changes. The campaign restarts (CPU only, about +5 s wall per
  run at speed 4). The current chain keeps flying meanwhile as early item 1 and 2 evidence. A confirmed item 1 or 2
  failure there still ends G3 as NOT PASSED.
- C. Keep the flights and score item 3 on the last 1.5 s of the 3 s hold. Not recommended: the window would be
  chosen after seeing the data.
Meanwhile: chain C212 flies for items 1 and 2, and its item-3 scores are not read or re-flown. G8 drafting continues.
Blocked: G3 item 3 rows only.
