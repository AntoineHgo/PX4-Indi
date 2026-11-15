# Questions to the owner

## Q1 (2026-11-15, session 13): confirm the outer-loop architecture (not blocking)

**Question.** Do you confirm candidate A as the architecture of the INDI outer loop that replaces `mc_pos_control`?

**Context.**
- Study: requirements checklist `design/outer_loop_requirements.md` (36 items + 15 from its review), three
  candidates (`design/outer_loop_candidates_r1.md`), amended in r2, r3, r4.
- Three independent review rounds (`design/outer_loop_review_r1..r3.md`): r1 fable, r2 and r3 opus. r2 found one
  BLOCKING issue (acceleration-only axes lose drag damping under INDI), closed by r3's design. r3 found no BLOCKING
  issue; its four MAJOR and four MINOR findings are answered in `design/outer_loop_candidates_r4.md`, with no
  interface change.
- **A (chosen):** `mc_indi_pos_control` is rewritten as a copy of the `MulticopterPositionControl` shell (take-off
  machine, constraints, failsafe setpoint, EKF resets, GotoControl). Stock `PositionControl` computes a_ref, and an
  INDI acceleration stage turns a_ref into the thrust vector at the local-position rate. Acceleration-only axes
  (Altitude xy, Descend, blind land) run the stock open-loop map. The stage tracks the commanded thrust while
  bypassed, so mode and ground edges are bumpless. There is no PID fallback (F-1). VTOL is not served.
- **B (deferred):** as A plus a fast INDI stage at IMU rate. It is a trigger change on A, taken only if G2's delay
  margin fails on A.
- **C (rejected):** own position law without stock `PositionControl`. It duplicates NaN-axis and limit logic that
  every mode depends on (r1 F10, F11).
- Cost: about 800 shell lines copied, stock modules at zero diff (O-11).

**Options.** (1) Confirm A (recommended). (2) Ask for B from the start. (3) Another review round first.

**Meanwhile.** Stage 1 (G1 evidence and simulator) continues. Stage 5 code does not start before your answer.
**Blocked:** no.

**Answer:**
