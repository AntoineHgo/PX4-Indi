# D-GAP review brief (S70, for an opus/fable reviewer in S71). One interface: decision text vs requirements and law.

Goal: independent review of the proposed outer-loop remedy for a steady command/output gap (decision 2), before any
code. Verdict BLOCKING / MINOR per finding, written to `design/dgap_review_r1.md`. About 12 tool calls.

Read only:
- `DECISIONS.md` section `## D-GAP` (the proposal) and `design/outer_loop_candidates_r3.md` section `## A11`.
- `results/stage5_s70/README.md` (the evidence table; flights single, seed 1).
- Rate-loop blend: `src/lib/indi_rate_control/IndiRateControl.hpp` lines 60-135 and the blend code in the `.cpp`
  (grep `_blend`). Outer law: `src/lib/indi_accel_control/` (header + update) and
  `src/modules/mc_indi_pos_control/McIndiPosControl.cpp` lines 95-215 (measured collective `_coll_meas`, `mean_u`).

Questions:
1. With coll_f = coll_meas + LP_tb(coll_model - coll_meas), is the steady z error zero for a 4-motor and for a
   single-motor thrust loss, through the actual chain (position P -> velocity P -> a_ref -> INDI collective)? What
   is coll_model in this module (commanded thrust through the actuator model?) and is it in the same units as
   mean_u-derived thrust (u = (omega/omega_max)^2, hover-thrust normalisation G = g/ht)?
2. Margin cost: loop structure at frequencies near 1/tb; lower bound on tb versus the outer-loop crossover so that
   phase margin >= 45 deg holds (G2). Relation to the stage-1 rate-loop blend failure at tb = 0.1 s.
3. Interaction with the hover-thrust estimator (HTE) still running in the module, with landed/bypass edges (A2/A8:
   blend must freeze, not reset, at bypass edges per A16), with telemetry loss (fallback to modelled state), and with
   saturation (blend windup when the collective clamps).
4. Is alternative (a) (per-motor command-to-omega^2 correction shared by both loops) clearly better for any gate
   (G3 weak motor, G6 transfer to other airframes)? Is (c) (stock velocity integrators) acceptable for upstream?
5. What test fails if the remedy is broken (lesson 20): name one unit test and one flight check.
