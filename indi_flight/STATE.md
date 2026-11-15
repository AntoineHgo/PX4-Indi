# STATE (max 150 lines)

## Status
- Stage: 1 (evidence and simulator), started session 1 (2026-11-15). Stage 0 done.
- Gates: G1 open | G2 open | G3 open | G4 open | G5 open | G6 open | G7 open | G8 open. GATES.md not yet written.
- Blocker: none. No owner question open.
- Outer-loop architecture study (MISSION section) runs in parallel with stages 1-3: not started.

## Next actions (in order)
1. Reference airframe (F-3): sourced data table `design/ref_airframe_data.md` (task T1, in flight / check result),
   then build the gz model `indi_flight`-owned (decide location: `Tools/simulation/gz` model dir vs bench overlay;
   firmware airframe file needed for SITL), check it flies with stock PID (one hover, one step).
2. Outer-loop study step 1: `design/outer_loop_requirements.md` from the `mc_pos_control` source (sonnet code read,
   one interface: source to checklist).
3. Write GATES.md for G1 before its first test.
4. Port bench runner/metrics into `indi_flight/bench/` with the review fixes (5 Hz held reference, decimated effort,
   ground-truth stamp, sim-time injections); self-test + second key per script. Errata re-score of set-O/T5.
5. Simulator items of stage 1 (delayed GNSS, rotor inertia, battery model, injectors, seeded drops, vibration,
   variants, noise profiles, determinism).

## Tasks in flight
| id | task | agent | output | resume |
|---|---|---|---|---|
| T1 | source reference 5-inch ~600 g quad physical data | sonnet | `design/ref_airframe_data.md` | re-launch with same brief if file incomplete |

## Open problems
- Review notes folder (`indi_project/review/external_review_s59_notes/`) not read in full at stage 0 (budget);
  open per item: `sim_review.md` for simulator work, `module_parity.md` for stage 3/5, `test_review.md` for stage 3,
  `ident_review.md` for stage 4, `remetric.py`/`hover.py` for the errata.

## Agent ledger (stage 1)
| session | id | model | task | outcome |
|---|---|---|---|---|

## Lessons proposed
(none)
