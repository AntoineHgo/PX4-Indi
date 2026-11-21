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

## Q23 (S189, 2026-11-21): G5.7 cause is aa4fd2654a (kept under D-JFF-KEEP at owner request). Which fix? BLOCKING for G5.7
Context: G5.7 fails 3/3 at freeze-9 on attitude tracking lag at hold edges (tilt_err 5.8-10.7 deg, limit 5; freeze-6
2.4-4.2; PID ref 4.50/4.54/7.50, s3 FAIL). Probes (results/freeze9_s183/g5_modes): XY gains back to freeze-6 values:
still FAIL (probe_s189); kSetpointLeadTc 0.01: still FAIL (probe_tc_s189); aa4fd2654a reverted (rate feed-forward in
every mode again): PASS s3 and s1, hold edges 2.5-3.8 deg (probe_ff_s189). aa4fd2654a was kept at your request
(D-JFF-KEEP) because the auto-mode a_ff is the stock smoother state that follows the vehicle: differenced, it fed
24-28 deg/s of rate FF during AUTO_LAND under strong vibration (results/g4_jff_s172). Without FF, INDI tracking lag at
hold edges (~48 ms) equals PID's (~50 ms), and PID also fails s3.
Options:
 A. FF in every mode except AUTO_LAND (and land-like failsafes): smallest change, keeps the S172 fix where it was seen.
    Probe first (G5.7 s3 + the S172 AUTO_LAND vibration case), then into FREEZE-10. Recommended.
 B. Full revert of aa4fd2654a: re-ships the AUTO_LAND FF defect.
 C. Keep aa4fd2654a: G5.7 stays NOT PASSED with this data (PID fails s3 too: your call whether G5.7 is a test defect).
Meanwhile: the G3 fix D-AF-ALIAS (outer-loop acceleration aliasing, INDI-only 7 Hz line) is implemented and probed;
both firmware changes would enter one FREEZE-10, then the invalidated rows are re-flown once. G5.7 work waits.
Blocked: G5.7 only.
