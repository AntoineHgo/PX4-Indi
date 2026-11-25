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

## Q32 (S225, 2026-11-25): draw 264 needs a firmware change after FREEZE-10. Re-freeze, exclude the corner, or stop? BLOCKING G3

Context (route check design/route_check_224.md; evidence results/g3_refly_actc_s212/restore264/):
- Draw 264 = available thrust 0.351 on all motors (sag) + one motor at 0.709, lemniscate. Q31 route steps 1-2 done.
- INDI on the gate binary 903eae63 at the frozen MC_INDI_ACT_BLD 1.0 loses control (ref264_s224/q0_bld100: watchdog,
  > 3 m below hold altitude). Same on the joint minimal case (falsifier_s222).
- Cause shown on logs (two investigators + falsifiers): the weak motor's torque bias grows with collective; the
  rate loop's only remover of a command/output gap is the 1 s blend of modelled and measured torque, too slow.
  ACT_BLD 0.15/0.10/0.05 or model-only (W_MAX 0) remove the loss of control (max tilt 45-54 deg).
- With tb 0.10/0.05 on draw 264 (blend264_s223) G3 item 1 passes but item 2 fails (post-fault 2 Hz p/q limit
  cycle, pre-fault clean) and item 3 fails (0.37/0.36 m vs 0.30 m).
- PID reference, same draw and binary (ref264_s224/README.md): item 1 pass (max tilt 41 deg), item 3 pass (0.123 m),
  item 2 FAIL both keys on the whole run (2 Hz q, windows straddling the fault; pre- and post-fault clean). So item 2
  fails in both stacks as scored today (a test-window question), while the INDI post-fault 2 Hz line and item 3
  are INDI-only. INDI tb 1.0 max tilt 66.8 deg before the abort.
- Any fix (lower ACT_BLD default, per-motor command-to-omega^2 correction, or a bounded rate integrator) changes
  frozen firmware/defaults: G2 rate/att cells, G3 (300), G4 (18), G5 rows, G6 item 7 are re-flown. Roughly 8-12
  sessions of CPU-heavy re-fly plus 1-2 sessions of design and two-key review.

Options:
- A. Re-open FREEZE-10 for decision 2 (D-RATE-BLD-2): one solver session (opus, high) + independent review compare
  (i) lower ACT_BLD, (ii) per-motor gain correction, (iii) bounded rate integrator on the four draws already flown
  (joint, 264, 262, 283) against a written pass line (items 1-3); pick one, check G2 rate margins, freeze-11, re-fly
  the listed rows.
- B. Keep FREEZE-10 and state the limit: amend G3 so the joint corner "sag below X + one weak motor" is outside the
  INDI claim (reported as a measured limit in the report, not a PID fallback, F-1), re-fly G3 on 903eae63 without it.
- C. Stop the G3 route: G3 NOT PASSED with this limit written up; go to G6/G7/G8 on FREEZE-10.

- Sub-question (any option): item 2 windows that straddle the fault instant also flag PID on this draw. Exclude
  windows straddling a fault from item 2 (score pre-fault and post-fault separately), yes/no? Recommendation: yes.

Recommendation: A, bounded: one solver session; if no option passes items 1-3 on the four draws, fall back to B.
Reason: the cause is a structural gap (no integral action against a growing actuator bias, lesson 9), which a real
weak or damaged motor also produces; B and C ship a known defect.
Meanwhile: nothing. Every open item (G3 campaign, G6 item 7, G7 F-10 clean-up, G8 chapters) depends on which firmware
is frozen. Blocked: yes (WAIT_OWNER).

Answer:
