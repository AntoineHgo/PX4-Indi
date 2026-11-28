# Re-review of chapter 4 (outer loop): fixes and chapter level

Reviewed: chapters/04_outer_loop.tex (current), diagrams/outer_loop.tex, diagrams/ground_logic.tex, against reviews/ch04_section_review.md, reviews/ch04_fixes.md, chapters/03_inner_loop.tex, firmware (src/lib/indi_accel_control, src/modules/mc_indi_pos_control, src/modules/mc_indi_rate_control), indi_flight/report/02_outer_loop_design.md, report/03_validation.md, DECISIONS.md, GATES.md. Line numbers are tex lines of 04_outer_loop.tex unless stated. Read-only.

## Part 1: status of R1-R17

| Id | Sev | Status | Check |
|----|-----|--------|-------|
| R1 | MAJOR | CLOSED | L261, L296-297, L369 checked at source. `IndiAccelControl::reset()` ("b is held, never reset") seeds filters and delay buffers with the measured mean u when finite, else `u_model - b`. `resetBlend()` is called only from `resetStageState()` (arm/disarm edges). The stage-restart call passes `fresh_esc ? mean : NAN` as the text says. Consistent with L296, L364, L369. |
| R2 | MAJOR | CLOSED | L235, L238, L406, table L429 checked at source: the rate module (`McIndiRateControl.cpp`) denies arming with "set MC_INDI_W_MAX"; the pos module treats `w_max <= 0` as invalid mean thrust. Fallback wording now covers only offline motor or stale ESC data. A remaining chapter-3 contradiction is C1; a nuance is C6. |
| R3 | MAJOR | CLOSED | L247-255, table row L227 checked. kMaxAge 20 ms (attitude, acceleration, commanded collective), kEscMaxAge 100 ms, kAllocMaxAge 200 ms, kAccRecoverTime 20 ms. Stage mode: Hold on stale attitude, modelled force on stale acceleration. `mean_u_valid = fresh_esc && !model_acc`, so a stale ESC only drops the measured thrust. The commanded-collective age only picks the restart value (`fresh_thr ? _collective_command : _last_thrust`). All five bullets match. |
| R4 | MAJOR | CLOSED | Chapter: T_col (L144-146, L148). Diagram outer_loop.tex: T_col at the split block, the plant arrow and the modelled-thrust block; no remaining non-bold T_c. No clash with the vector T_c. |
| R5 | MINOR | OPEN (diagram) | The chapter uses tau (L87, L146, L196, L199). diagrams/outer_loop.tex still has `.../c` in the jerk block (`\omega_ff = (j.y_b, -j.x_b)/c`). The symbol c is undefined in the chapter and clashes with the ch03 lead coefficient c, which was the point of R5. Fix: replace `/c` with `/\tau`, or `/\lVert\mathbf{T}_c\rVert`. |
| R6 | MINOR | CLOSED | `\ts` in L270, delta in L115, u_meas,f explained L273. See C4 for the remaining u_f overlap. |
| R7 | MINOR | CLOSED | L99-112. |
| R8 | MINOR | NEW (partly) | Text L360 and diagram caption now say "4 to 5 % (limit 10 %)": the diagram is closed. But the 4.0-4.7 % comes only from the take-off after re-arm test (validation G5.9d). The other take-offs (G5.4) are verified only as "<= 10 %". L360 "On the measured take-offs it was 4 to 5 %" and the diagram note present one test as all take-offs. Fix: "In the take-off after a re-arm the step was 4 to 5 % of the hover thrust; every take-off stayed below a limit of 10 %." Same in the diagram note ("measured step 4 to 5 % in the re-arm take-off, limit 10 %"). |
| R9 | MINOR | CLOSED | L378-379 design reason given, history gone. "In simulation" is attached only to the 2 deg (see C8). |
| R10 | MINOR | CLOSED | L165-166. 95.73 - 88.89 = 6.84 Hz. See C5 for the stage trigger. |
| R11 | MINOR | CLOSED | L57. |
| R12 | MINOR | CLOSED | L225, L400. `kStageDtMin` 2 ms clamp, `kStageDtMax` 0.2 s hold. |
| R13 | MINOR | CLOSED | L347, L354, L366 agree with the review's source checks. |
| R14 | MINOR | CLOSED | L138-140. |
| R15 | MINOR | CLOSED | L199, L236, L443; `kMinThrustForFf` 1.0 in the header. |
| R16 | MINOR | CLOSED | L37, L337-338. |
| R17 | MINOR | CLOSED | L281-285 (rho argument). Derived independently: with T_f = measured thrust and rotor state a fraction rho of the commanded state, steady state gives a_f = a_ref - (1 - rho) T_c with T_c = a_ref - g. A wrong g_t gives g_r u = a_ref (no offset). Both statements are correct. |

Part 1 totals: CLOSED 15, OPEN 1 (R5, MINOR, diagram), NEW 1 (R8 scope, MINOR). No MAJOR left open. No new development trail (grep of chapter and both diagrams for decision ids, session/question numbers, file names, code line references, gate ids: no hits).

## Part 2: chapter level (directive item 7b)

Reasoning flow is good: problem (model-based thrust, slow integrator), idea (measure, add the error), three questions, design sections in the promised order, then modes, ground, resets, guards, parameters, pointer to the analysis chapter. Cross references resolve (eq:u_state, eq:indi_law, sec:indi_principle, ch:analysis, ch:inner_loop exist). All tables and both figures are referenced.

### C1 MAJOR - ch03 contradicts ch04 on MC_INDI_W_MAX = 0 (chapters/03_inner_loop.tex L175, L350)
ch03 L175: "Setting MC_INDI_W_MAX to 0 turns the measured path off." ch03 table L350: "0 turns the measured path off." ch04 (L235, L429) and ch03 L312 and L326-area guards say a zero value blocks arming. A reader of ch03 will think the INDI rate loop can fly without rotor telemetry. Fix (in ch03, not ch04): L175 "MC_INDI_W_MAX must be set. With its default of 0 the rate module refuses to arm, because no measured torque can be built." Table L350 meaning: "Rotor speed at full thrust. Must be set; the default 0 blocks arming."

### C2 MINOR - figure 4.1 is thinly explained (L92-94, caption L90)
The text after the figure has three sentences. Not explained in text or caption: the "H" badges (the matched low-pass filters of the filter section), the "Force source" switch, the dashed/coloured measured versus modelled paths, and the thrust-state block. Fix: add after L94: "The blocks marked H are the matched low-pass filters of \cref{sec:outer_filters}. The force-source switch selects the measured force (flight) or the modelled force (ground, take-off ramp, stale data) as described in \cref{sec:outer_state}. The thrust-state block forms T_f from the measured and the modelled rotor state with the blend of \cref{sec:outer_gap}." Check that the colour convention is stated in the caption (measured versus modelled). Likewise \cref{fig:outer_ground} gets one sentence (L340): add that the edge note applies to the step discussed under "Edge to flight".

### C3 MINOR - roadmap does not list the thrust-gap problem (L24-31)
The opening problem is a real thrust gap (battery, weak motor) and the integrator. The three questions do not include how the gap is removed, which is the subject of section 5 and the "key result". Also the section on measured and modelled state (section 4) is not in the announced order. Fix: add a fourth item "How is a standing thrust gap removed without an integrator?" and end with "Later sections cover the modes, ...".

### C4 MINOR - symbol overlaps with chapter 3 (L87, L130-136, L273)
(a) tau is the thrust magnitude here; ch03 uses tau_a for the actuator time constant. Subscript distinguishes them but a reader who skims will mix them. Suggest "thrust magnitude $\tau$" is kept and a sentence, or rename to $T_\mathrm{n}$. (b) u_f is a scalar here and the filtered torque vector in ch03. L273 explains this for u_meas,f only, while u_f appears first at L134-136. Fix: at L136 "...of all rotors (a scalar; in \cref{ch:inner_loop} u_f is the torque)". (c) u_mod,f is the filtered commanded collective here and the filtered output of the actuator model in ch03; both are "model path", just say "(the model path of the thrust)". (d) t_b is the blend time constant in both chapters with different parameters (MC_INDI_ACT_BLD, MC_INDI_POS_TB); acceptable, no change needed.

### C5 MINOR - what triggers the stage is never stated (L161-166)
L162 says the module is scheduled on the acceleration topic and handles every sample, L166 says the stage runs at about 89 Hz. A reader sees a contradiction. In firmware the force filter runs on every acceleration sample while the stage (the INDI law) runs when the position estimate updates. Fix: "The force filter runs on every acceleration sample. The stage itself runs once per update of the position estimate, about 89 Hz in the reference simulation."

### C6 MINOR - the "W_MAX 0 blocks arming" statement needs its condition (L235, L429)
The block comes from the rate module and applies when the INDI rate module is enabled. With only the outer loop enabled, W_MAX 0 gives no measured thrust and the stage runs on the modelled thrust without refusing to arm. Fix: "With its default of 0 the INDI rate module refuses to arm, and the outer loop has no measured thrust." Table: "Must be set; the default 0 blocks arming of the INDI rate loop."

### C7 MINOR - equations are not referenced by number (L81, L134, L146, L196, L270)
Equations eq:outer_fb, outer_gt, outer_cmd, outer_blend and outer_ff are never cited with \cref in the text (only eq:outer_inc, outer_vsp, outer_aref are). The task rule is that each equation is referenced and explained. Fix: add one \cref where each is introduced, for example "...the force $\vect f_b$ of \cref{eq:outer_fb}" in L83, and in the guards and diagram caption (T_col of \cref{eq:outer_cmd}, blend of \cref{eq:outer_blend}, feed-forward of \cref{eq:outer_ff}).

### C8 MINOR - simulation-specific numbers (L378)
"vibration of about 0.25 m/s^2, against 0.04 m/s^2 after the filter" is a simulation measurement, as the review said. Fix: "In the reference simulation a single raw accelerometer sample carries vibration of about 0.25 m/s^2 ...". Also L360/L165 already mark simulation; keep consistent.

## Counts
- Part 1: BLOCKER 0, MAJOR 0 open, MINOR 2 (R5 open, R8 new); 15 of 17 closed.
- Part 2: BLOCKER 0, MAJOR 1 (C1), MINOR 7 (C2-C8).
