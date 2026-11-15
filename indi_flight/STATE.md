# STATE (max 150 lines)

## Status
- Stage: 1 (evidence and simulator), started session 1 (2026-11-15). Stage 0 done.
- Gates: G1 open | G2 open | G3 open | G4 open | G5 open | G6 open | G7 open | G8 open. GATES.md: G1 draft written (not tested).
- Blocker: none. No owner question open.
- Outer-loop architecture study (MISSION section) runs in parallel with stages 1-3: not started.

## Next actions (in order)
1. Reference airframe (F-3): table `design/ref_airframe_data.md` done (T1): 0.610 kg 4S, I = 1.4/1.5/2.7e-3,
   arm 0.0795 m, kT 1.5e-6, kQ/kT 0.0127 m, w_max 2800 rad/s, tau 33 ms, J_rotor 5e-6 (ASSUMED), 14 poles,
   T/W 7.9, hover ~1000 rad/s (u ~0.13). Second key T2 (arithmetic + SDF mapping, no web) done: `design/ref_airframe_check.md`, 10 WRONG items to apply
   before the model is written (THR_MDL_FAC 1 / EC_MIN 0 / MPC_THR_HOVER 0.127; w_max 2694 at 14.8 V; rolling moment
   ~5e-8 or 0; rotor izz used at w/10 so spin-up torque 1/10: confirm in gz). Source re-check (web) still pending. Note kT varies
   ~20 % hover to full speed (thrust curve is not pure omega^2: matters for decision 3 and THR_MDL_FAC). Then build the gz model in `indi_flight/sim/models/` (D-2) plus a SITL airframe file, check it flies with stock PID (one hover, one step).
2. Outer-loop study step 1: `design/outer_loop_requirements.md` from the `mc_pos_control` source (sonnet code read,
   one interface: source to checklist).
3. Write GATES.md for G1 before its first test.
4. Port bench runner/metrics into `indi_flight/bench/` with the review fixes (5 Hz held reference, decimated effort,
   ground-truth stamp, sim-time injections); self-test + second key per script. Errata re-score of set-O/T5.
5. Simulator items of stage 1 (delayed GNSS, rotor inertia, battery model, injectors, seeded drops, vibration,
   variants, noise profiles, determinism).

## Session 2 end note (budget)
- T3 and T4 were still running when the session hit its cap. On disk, UNCOMMITTED and UNVERIFIED: `sim/models/quad5in{,_base}`,
  `ROMFS/.../airframes/4040_gz_quad5in` + CMakeLists entry, `bench/`, `results/` (T3). T4 had written nothing at $2.0.
  Next launch: check `git status`; if `design/ref_airframe_model.md` / `design/outer_loop_requirements.md` exist, review
  them, else relaunch with a 20-call brief. Read the T3 diff before committing (firmware/ROMFS commit separate from sim).
- Lesson proposed: two sonnet agents cost ~$1.4 together in 30 min here; at a $3 cap launch one agent per session.

## Tasks in flight
| id | task | agent | output | resume |
|---|---|---|---|---|
| T3 | gz model + SITL airframe for ref airframe, PID hover/step check (D-3) | sonnet | `sim/models/`, `design/ref_airframe_model.md` | relaunch with brief in JOURNAL S2 if file incomplete |
| T4 | outer-loop requirements from mc_pos_control source | sonnet | `design/outer_loop_requirements.md` | relaunch if incomplete |

## Open problems
- Review notes folder (`indi_project/review/external_review_s59_notes/`) not read in full at stage 0 (budget);
  open per item: `sim_review.md` for simulator work, `module_parity.md` for stage 3/5, `test_review.md` for stage 3,
  `ident_review.md` for stage 4, `remetric.py`/`hover.py` for the errata.

## Agent ledger (stage 1)
| session | id | model | task | outcome |
|---|---|---|---|---|
| 1 | T1 | sonnet | sourced airframe data | done, 42 calls, ~$1.0 (above 30-call brief) |
| 1 | T2 | sonnet | second key, arithmetic/SDF | done, 14 calls, ~$0.8, 10 WRONG items |

## Lessons proposed
- Web-research agents cost about 3x a code-read agent of the same call count; brief them at 20 calls.
