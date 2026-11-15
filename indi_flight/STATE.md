# STATE (max 150 lines)

## Status
- Stage: 1 (evidence and simulator), started session 1 (2026-11-15). Stage 0 done. Session 3: ref airframe model done.
- Session 4 (launch 20261115-175831): requirements reviewed, candidates r1 drafted, fact 1 closed. Route check due S5.
- Gates: G1 open | G2 open | G3 open | G4 open | G5 open | G6 open | G7 open | G8 open. GATES.md: G1 draft written (not tested).
- Blocker: none. No owner question open.
- Outer-loop architecture study (MISSION section) runs in parallel with stages 1-3: not started.

## Next actions (in order)
1. Reference airframe model DONE (session 3): `design/ref_airframe_model.md`, flies with stock PID (hover u 0.1367,
   eRPM 998.7 rad/s, steps settle). Its open items 1-4 (reaction-torque scaling test, gyro log rate, run1 esc_rpm 0,
   run-to-run spread) are folded into the simulator work of item 4.
2. Outer-loop study: step 1 DONE (T4, `design/outer_loop_requirements.md`, R1-R36). Requirements review T5
   launched S4 (output `design/outer_loop_requirements_review.md`): merge its BLOCKING items into the
   requirements file. Step 2 round-1 draft DONE S4: `design/outer_loop_candidates_r1.md` (A single-rate shell
   copy + stock PositionControl kinematics with I=0 + INDI stage; B dual-rate; C own law; R-a/b/c rejected).
   T5 DONE S4: 15 new items (4 BLOCKING, inherited by A/B via the shell copy), R9 corrected; candidates
   re-checked. Fact 1 CLOSED S4: local position 125 Hz in SITL -> A preferred. Rnew items folded as R37-R51
   (S4). NEXT: (b) review round 1, fable, ~$1.2, launch at session
   start: brief = candidates_r1 vs requirements(+review) + source, find the mode/transition each candidate breaks,
   output `design/outer_loop_review_r1.md`; (c) round 2, then owner question with one-page summary.
   Defect: rc.mc_apps starts mc_pos_control unconditionally (line 49), MC_INDIP_EN adds the INDI module: R1 fails.
3. Write GATES.md for G1 before its first test (draft exists).
4. Port bench runner/metrics into `indi_flight/bench/` with the review fixes (5 Hz held reference, decimated effort,
   ground-truth stamp, sim-time injections); self-test + second key per script. Errata re-score of set-O/T5.
5. Simulator items of stage 1 (delayed GNSS, rotor inertia check, battery model, injectors, seeded drops, vibration,
   variants, noise profiles, determinism). Source web re-check of J_rotor (ASSUMED) still pending.

## Tasks in flight
| id | task | agent | output | resume |
|---|---|---|---|---|
| - | none | | | |

## Open problems
- G1 logging: vehicle_acceleration logged at 20.8 Hz in T3 (logger cap, SDLOG_PROFILE 17); the outer-loop
  analysis needs it at the controller rate. Fix in the bench logging profile.
- Review notes folder (`indi_project/review/external_review_s59_notes/`) not read in full at stage 0 (budget);
  open per item: `sim_review.md` for simulator work, `module_parity.md` for stage 3/5, `test_review.md` for stage 3,
  `ident_review.md` for stage 4, `remetric.py`/`hover.py` for the errata.

## Agent ledger (stage 1)
| session | id | model | task | outcome |
|---|---|---|---|---|
| 1 | T1 | sonnet | sourced airframe data | done, 42 calls, ~$1.0 (above 30-call brief) |
| 1 | T2 | sonnet | second key, arithmetic/SDF | done, 14 calls, ~$0.8, 10 WRONG items |
| 2 | T3 | sonnet | gz model + PID check | done (verified and committed in session 3) |
| 2 | T4 | sonnet | outer-loop requirements | cut by cap, nothing written |
| 3 | T4 | sonnet | outer-loop requirements, relaunch | done, 31 calls, ~$0.75, 36 items, 305 lines |
| 4 | T5 | sonnet | requirements review | done, 16 calls, ~$0.5, 15 new items (4 blocking) |

## Lessons proposed
- At a $3 cap launch one agent per session (session 2: two sonnet agents ~$1.4 in 30 min, both cut).
- Web-research agents cost about 3x a code-read agent of the same call count; brief them at 20 calls.
