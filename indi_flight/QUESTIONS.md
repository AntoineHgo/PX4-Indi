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

## Q27 (S207, 2026-11-22): Q26 check results; choose the tau box, K rule, pre-identification item, FREEZE-11
BLOCKING for G3 (box and test text), and through it for G6, G7, G8. Results: results/q26_actc_s207/README.md (table),
results/q26_kscale_s207/README.md, results/q26_264_s207/README.md. FREEZE-10 binary throughout, params overrides only.
1. Re-fly, 8 S199 draws at speed 1 (S199 INDI -> set a ACT_TC = drawn tau_slow -> set b 1.5 x tau_slow), keys k1/k2:
   245 (C1, LOC) ABORT -> PASS/PASS -> PASS/PASS; 239 (B) FAIL 2 Hz 76 dps -> PASS/PASS -> PASS/PASS;
   283 (A: fast motor, 10 ms) FAIL 10.75 Hz 18 dps -> PASS/PASS -> FAIL/FAIL 10.75 Hz 9-13 dps (PID passes);
   008 (A) FAIL 10.75 Hz -> k1 FAIL 2.0 Hz 10.5, k2 PASS -> FAIL/FAIL 10.75 Hz 6-7 (PID fails it harder, 161-207 dps);
   046 (D) FAIL both -> k2 FAIL 2.0 Hz 13.4 -> PASS/PASS; 240 (class C) k1 FAIL -> k1 FAIL -> PASS/PASS;
   039 land wall timeout (harness, both stacks) in every set, scored PASS; 264 ABORT tilt > 60 deg in both sets.
   So an identified ACT_TC removes the slow-motor LOC and the 2 Hz class B; the round-up end (x1.5) keeps the
   fast-motor class A line (lower RMS).
2. Model (MARGINS_S200 method, worst over the realised G3-box corners, PM deg / GM dB): ACT_TC 0.033 fixed 5.7 / 3.1;
   ACT_TC = tau, K 20: 35.9 / 6.8; ACT_TC = 1.5 tau, K 20: 36.2 / 5.3. K scaled with 1/tau_c: 13.8 / 1.4 (a), 33.3 / 3.1 (b),
   worse in both (K reaches 40 on fast motors; 283 GM 9.5 -> 3.2 dB). No rule gives PM 45 on every corner (binding:
   tau x3 + 10 ms + G1 error 1.2). G2 is measured on the nominal plant and is not affected.
3. 264 (log only): a 20 ms collapse of both CW rotor speeds (11600 -> 7000 rpm, command flat) hits both stacks; no
   saturation, no unallocated torque. INDI's pitch/roll counter-torque is 55-80 % of PID's for 0.2 s; the rate setpoint
   reaches 220 dps; tilt > 60 deg. Likely (not shown): low rate-loop gain against a large disturbance. Unexplained: why
   the rotors collapse (injector or Gazebo model at speed scale 0.351; not traced).
4. Class C: Q15 A (skip windows overlapping the 3 s after a nav_state change) is written for G4 only; G3 key 2 applies
   it, key 1 (g3_score.sh) does not. Proposed rule: Q15 A applies to G3 item 2 for both keys (transitions are judged by
   G5); key 1 re-scored with its existing --skip-nav-change. Freeze-10 item 2 drops from 79 to at most 54 runs:
   verdict unchanged (NOT PASSED).
Options and recommendation:
- C1 (recommended): tau becomes identification error, one-sided ACT_TC / tau_slow in U[1, 1.5] with up/down asymmetry
  kept; K fixed 20 (no 1/tau_c scaling: the model rejects it); x0.5..3 result reported as the unidentified limit. No
  firmware change, so FREEZE-10 and G2, G4, G5 stand; only the 300-run G3 campaign is re-flown (tooling: draw the
  controller ACT_TC like the controller G1 error, about 8 h CPU), with the class C rule above. Risk, stated now: class A
  draws near the x1.5 end may still fail item 2 (283, 008 set b), and 264 still fails item 1.
- C2: as C1 with [1, 1.2] (tighter identification claim). Removes 283 at the cost of a stronger bring-up requirement.
- B: close G3 NOT PASSED as written, report this check as the path; go to G6-G8.
264 (needs your call whatever the box): (i, recommended) one session: confirm the rotor collapse is the drawn fault,
then a params-only probe of MC_INDI_K_R/P 30 and 40 on 264 with model margins; if it recovers with margins kept, the
new default is FREEZE-11 (firmware default change, re-flies G2, G4, G5 and G3); (ii) report 264 as a limit.
Pre-identification state (ID_OK 0, gains x0.5, ACT_TC 0.05): recommend a G6 item "flies the x0.5..3 tau box without
LOC" on a reduced set (the 8 draws plus the 16 box corners, item 2 reported, not required), not a second 300-run campaign.
Meanwhile: nothing (route check 207: every gate item waits on this answer). Blocked: yes, WAIT_OWNER.
