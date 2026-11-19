# Route check 133 (written for S134)

Read: STATE.md, ANOMALIES.md, DECISIONS.md 601-719 (headings + last 60 lines), JOURNAL.md last 15 lines,
design/g5_build_list.md 91-140. Nothing else. Line numbers below are from those reads.

## (1) Is stage 5 still on the shortest path to G2-G8?
Mostly yes, with one drift. Stage 5 is needed: G3 evidence for the INDI outer loop needs MC_INDI_POS_EN=1
(STATE.md:17-18), ACRO is carried by G5 (STATE.md:22), and D-IDENT-STOP freezes identification until stage 5 has
multi-mode code (DECISIONS.md:657). The mode rows T1-T10 are now built and probed (STATE.md:45-69).
Drift: all of G2-G8 are still open (STATE.md:6) and G5 has no section in GATES.md (STATE.md:13, 69). Four sessions
(S130-S133) went into build rows plus two handover-edge anomalies (A-45, A-46; ANOMALIES.md:30), while the probes
are still called "probes, not gate evidence" (STATE.md:17). The path is short only if the G5 pass criteria are
written first. Without them, further build work has no stopping rule.

## (2) Which recorded decision is the main difficulty a consequence of?
D-STAGE-STALE (DECISIONS.md:686-705), line 698-700: `want_indi` false keeps the STOCK path on ground and takeoff
ramp. The vehicle therefore runs two controllers (stock integrator, INDI stage) with a switch at every edge.
- A-45 (25 % thrust step) was the stock integrator zeroed at the edge; fixed by D-HANDOVER (DECISIONS.md:707-719).
- A-46 (6.1 % step at the ACRO rampup->flight edge, ANOMALIES.md:30) is the same class: a state carried across
  the edge, not a new bug.
- T9 (hover-thrust port, STATE.md:62) is a third patch of the same seam.
Underlying choice: module = fork of mc_pos_control + INDI stage (JOURNAL S129 line), base A (STATE.md:7).
D-HANDOVER:716-717 rejected "start INDI already in rampup" on the ground-reaction argument, which is the choice
that keeps the seam alive.

## (3) What a fresh start on this stage would do differently
- Write the G5 section of GATES.md (mode x metric x threshold, incl. edge step limit, e.g. 10 % of hover) BEFORE
  any build row; STATE.md:13 asked for it before S130 and it is still not done.
- Treat the edge (stock -> INDI) as one pure, unit-tested state machine owning every carried state (integrator,
  a_ref offset, hover thrust, blend, reset counters), instead of D-STAGE-STALE + D-HANDOVER + T9 + T10 as separate
  patches. Candidate: a single `EdgeState` helper with a gtest table of edges.
- Define the PID reference step per edge once (S131 measured 0.0075, STATE.md:55) and use it as the pass line,
  so each edge is a table row, not an anomaly.
- Probe all modes in one batch on 3 seeds, not 1 seed per mode per session (A-46 closing test is already 3 seeds).
Not changed: base A, F-1 no-fallback rule, D-IDENT-STOP.

## (4) Next 3 actions, in order
1. Write the G5 section of GATES.md: per-mode metrics, thresholds, edge-step limit, seeds, what counts as a pass.
   Output: indi_flight/GATES.md (G5 section) plus a 10-line note design/g5_criteria_s134.md.
2. Run T11 as one batch, 3 seeds, INDI vs PID reference, all modes flown so far plus the unflown rows
   (accel-only offboard, offboard takeoff, MANUAL/STABILIZED, STATE.md:66-67) with bench/t9_step_check.py;
   this is also the A-46 closing test. Output: results/g5_probe_s134/README.md (table mode x pass/fail x metric)
   and the A-46 row updated in ANOMALIES.md.
3. Decide from that table whether edge steps are one cause: if two or more edges fail, write the EdgeState
   design (carried-state inventory, gtest table) before any further patch; if not, close A-46 and move to the G2
   offline todo (STATE.md:19-20). Output: design/edge_state_s134.md (or an ANOMALIES.md closure entry) and the
   updated STATE.md next-actions.

## Orchestrator response (S133)
ACCEPTED: actions 1-3 in order (G5 section of GATES.md first, one 3-seed T11 batch closing A-46, edge-state
note if >= 2 edges fail). REJECTED: "PID reference step as the pass line" contradicts F-5 (no gate is relative to
PID); G5 transient limits are absolute physical values, PID flies alongside for reading only.
