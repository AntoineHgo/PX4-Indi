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

## Q24 (S194, 2026-11-21): G3 pre-test at FREEZE-10, four draws fail (BLOCKING for G3 only)
Context. FREEZE-10 pre-test (results/freeze10_s193/g3_pretest/README.md, 20 draws, seed 173): key 1 16/20, key 2
16/20, both keys fail 02, 03, 05, 08 (item 2 = sustained oscillation, item 3 = steady xy error).
- 02/05: GNSS latency uncompensated by +95/+84 ms (GATES l.289 draws latency + U[-100,+100] ms in 50 % of runs).
  q ~1.45 Hz accel-loop oscillation (detector reports its 2.0 Hz band floor), 13-16 dps, xy error ~0.49-0.5 m.
  S192 probe: same draws with matched GNSS pass items 1-3 both keys. PID passes 02/05 (S187 refs). INDI-specific,
  cause shown: the outer loop (D-OFFB-POSVEL, XY gains 1.2/2.4) is less tolerant of a stale position than PID.
- 03 (+20 ms): INDI q 2.0-2.5 Hz, 19-20 dps. PID ref: key 1 FAIL (q 2.5 Hz), key 2 PASS.
- 08 (-63 ms): INDI q 10.75 Hz ~9 dps; PID fails both keys (p 11 Hz, r 8 Hz). Shared with PID.
Options.
 A. Keep the gate. After the queue ends, probe 02/05 (and 03) with lower XY_P/VEL_P (config only). If they pass and
    the G5.5/G5.7 probes hold, declare FREEZE-11 and re-fly G2 outer/G4/G5 outer (~4-5 h CPU, ~2 sessions).
 B. Narrow the mismatch to U[-50,+50] ms and add "EKF2/SENS GNSS delay set within 50 ms of the measured
    latency" to the F-3 requirements and bring-up checklist. Gate change after first test: your call only.
 C. Keep the gate and the gains; G3 NOT PASSED for uncompensated GNSS latency above ~+60 ms, stated as a limit.
 For 08 (and 03 key 1): count as a scenario property shared with PID (reported, not an INDI failure), or count.
Recommendation: A for 02/05/03 (honest fix, config only); 08 reported as shared with PID, not counted against INDI.
Meanwhile: the queue (G5, G4, G2 outer) runs on; no G3 re-fly, re-score or note until answered. Not blocked overall.

**Owner answer to Q24 (2026-11-22):** B for 02/05, and 08 (and 03 key 1) reported as shared with PID.
1. Narrow the EKF GNSS delay mismatch draw to latency + U[-50, +50] ms (min 0); matched/mismatched split stays
   50/50. Add "EKF2/SENS GNSS delay set within 50 ms of the measured GNSS latency" to the F-3 requirements and to
   the bring-up checklist. Record the gate change in GATES.md as an owner amendment (date, Q24 B), with the reason:
   the +-100 ms mismatch exceeds what a correct bring-up leaves, and the S192 matched-GNSS probe shows 02/05 pass.
2. No firmware or config change: FREEZE-10 stands, G2/G4 verdicts stand.
3. 08 and 03 key 1 fail with PID on the same draws: reported in the G3 evidence as scenario properties shared
   with PID, not counted against INDI.
4. How to re-run the pre-test under the new range (re-draw vs. re-fly only the affected draws) is the agent's to
   plan; state the plan in a decision before flying, and keep the earlier 16/20 result in the evidence.

## Q25 (S194, 2026-11-22): G5.5 o2_circle_z s1 fails by 3 mm, PID fails by 0.65 m (BLOCKING for G5 only)
Context. FREEZE-10 G5 re-fly (results/freeze10_s193/G5_SCORES.md): every flown G5 row passes both keys except G5.5
o2_circle_z s1: horizontal RMS truth vs analytic reference 0.5027 m, limit 0.5 m (both keys agree; s2 0.491, s3
0.496; freeze-9 0.488/0.497/0.499 PASS). PID reference, same scenario, seeds and nominal plant
(results/freeze10_s193/g55_pid_ref/README.md): 1.157/1.144/1.146 m, no LOC. The 0.5 m limit is the G3 steady-state
xy limit applied to a moving trajectory (GATES l.462); Q11 B kept it. Coupling: Q24 option A (lower XY gains for the
GNSS-mismatch draws) would most likely raise o2 tracking error further.
Options.
 A. Keep 0.5 m: G5 NOT PASSED on one cell (0.6 % over), all other rows pass; stated as a limit in the report.
 B. Declare the row a test defect (absolute 0.5 m on a circle no reference stack meets) and set a trajectory limit
    sourced from the scenario (e.g. speed x one outer-loop time constant); re-score only, no re-fly.
 C. Keep 0.5 m and accept a tuning change (config) that improves o2 tracking, folded into a FREEZE-11 with Q24.
Recommendation: A (no threshold change after the test to pass a row by 3 mm); B only if you judge the limit wrong
for both stacks. Meanwhile: no G5 re-fly, re-score or note; G2 verdict proceeds. Not blocked overall.

**Owner answer to Q25 (2026-11-22):** B. The absolute 0.5 m horizontal limit is a test defect for moving
offboard trajectories (a steady-state hover limit; no reference stack meets it on o2: PID 1.14-1.16 m).
1. Replace it for the G5.5 trajectory segments with a limit derived from the scenario (e.g. reference speed x one
   outer-loop time constant, or another sourced bound). Write the derivation and its sources in a decision and in
   GATES.md as an owner amendment (date, Q25 B) BEFORE re-scoring; the limit must not be picked from the scores.
2. Apply the same limit to every G5.5 row and to the PID reference; report both stacks against it.
3. Re-score only, no re-fly. Vertical 0.3 m and the offb_vel_step rows are unchanged.
