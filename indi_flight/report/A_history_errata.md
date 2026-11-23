Status: draft complete

# Appendix A. History and errata

This appendix tells a reader of the design chapters how the design got to its current state and which earlier numbers
were wrong. Paths are relative to the repository root unless they start with `indi_flight/`. `S<n>` is a session of
`indi_flight/JOURNAL.md`; `D-...` are entries of `indi_flight/DECISIONS.md`; `Q<n>` are owner questions (full text in
`indi_flight/JOURNAL.md`, open ones in `indi_flight/QUESTIONS.md`). Decision ids are cited in this report only.
The archive `indi_project/` is read-only (F-4) and was not touched.

## A.1 The first project (archive, 59 sessions)

**What it built.** A benchmark of an INDI rate controller (`mc_indi_rate_control`, final version `indi_v3`) and an INDI
position controller (`indi_pos_v3`) against a tuned PID stack in PX4 SITL (Gazebo, x500 and a 5-inch class model). Its
question was "does INDI outperform PID under four pre-registered criteria". It answered "no" three times (stages 2b and
8, hover-effort criterion) (`indi_project/review/external_review_s59.md` sec. 1, item 1).

**Why its evidence did not support a flight.** The external review after session 59 (2026-11-15, same file) found that
no criterion measured flight readiness (margins, robustness envelope, mode and failsafe coverage, loop rates, a loadable
parameter set). The primary trajectory metric was computed against a 5 Hz reference held between samples, which scored
a 100 ms lagging vehicle better than a perfect tracker (sec. 2.1, [verified]). The criterion that failed stages 2b and 8
measured 0.1 % of full-scale motor command in a simulator quieter than a real vehicle (sec. 2.2). Both final controllers
had been validated only on sets built around the previous version's weakness (sec. 3.3). The outer loop probably had
no integral action against a command/output thrust gap (sec. 5.1, [derived], not flown). Firmware defaults were not a
validated configuration (G1 320/210/30, `MC_INDI_W_MAX` 0, `MC_INDI_ACT_BLD` 0, `MC_INDI_YAW_CUT` 0; sec. 2.3).

**Owner decisions that started this project** (`indi_project/review/external_review_s59.md` sec. 0, 2026-11-15, and
`indi_flight/DECISIONS.md` lines 6-26; F-7 to F-10 from `indi_flight/MISSION.md` lines 71-87):

| id | decision |
|---|---|
| F-1 | No PID fallback; INDI runs alone, robustness shown by margins (G2) and the robustness campaign (G3). |
| F-2 | INDI serves every flight mode and failsafe; offboard-only is not the end state. |
| F-3 | Generic architecture for quadcopters with eRPM telemetry; evidence on one simulated 5-inch, ~600 g reference airframe. |
| F-4 | `indi_project/` is never modified; corrections go to `indi_flight/results/errata.md` and the report. |
| F-5 | PID is a reference, never a pass condition; no gate is a ratio to PID. |
| F-6 | The outer loop replaces `mc_pos_control`, started instead of it by parameter. |
| F-7 | One controller from arming to disarming (2026-11-20). |
| F-8 | Two G5 test rows dropped: accel-only offboard and take-off on an offboard setpoint alone (2026-11-20). |
| F-9 | Direct path, simple means (2026-11-20). |
| F-10 | Delivered code reads as upstream PX4 code (2026-11-22); clean-up as separate behaviour-neutral commits. |
| O-11 | Separate modules behind Kconfig; stock rate, attitude, position, allocation and commander at zero diff against `main`. |

The review also withdrew the PID-fallback gate, asked for a fresh start on reusable code with the archive preserved
(sec. 0), and the project began with a new simulator model, stage 1.

## A.2 Timeline by stage

Stage definitions: `indi_flight/MISSION.md` lines 266-307. Session ranges are those recorded in the journal; stages
overlapped (the stage-5 hover slice was coded in S60 while stage 3 was open).

| stage | sessions | main result | freezes |
|---|---|---|---|
| 1 evidence, simulator | to S35 | quad5in model and runner; G1 (simulator evidence) frozen "FINAL with evidence limits" S36 under Q4-A; G1 PASSED S84 | none |
| 2 analysis tools | S36-S55 | loop-gain injection in SITL, linear models, G2 text written S40, rate-loop flights S41-S42 | none |
| 3 inner loop | S56-S118 | stage 3 recorded OPEN S56 (JOURNAL line 463); landed handling, frozen-rotor detection, setpoint timeout (D-S3-LANDED, D-S3-FROZEN, D-S3-SPTO, S58); rate lead D-RATE-LEAD (S48 proposed, S53 defaults) | none |
| 4 identification | S119-S126 | stage 4 opened S119 (`design/ident_concept.md`, Q6 answered B); D-IDENT-STOP S126 froze identification until the outer loop had multi-mode code | none |
| 5 outer loop, all modes | S60 slice, S128-S153 | hover slice flew S60 (T122); multi-mode build S128-S131 onward; G5 injectors and tests S136-S151; pre-freeze reviews r1-r3 S152-S155 | none |
| 6 validation | S155-present | G2, G3, G4, G5 on the frozen pair | FREEZE-6 to FREEZE-10, below |
| 7 packaging | S195-present | G7 items (a)-(f) worked S195-S196 (`indi_flight/results/g7_s195/`); G8 drafts S215 | none |

Freezes (all in `indi_flight/DECISIONS.md`; numbering starts at 6, the stage-6 freeze):

| freeze | session, firmware | what changed |
|---|---|---|
| FREEZE-6 | S155, 23acbdef67 | first stage-6 freeze: firmware, identified parameter set (`ID_OK 1`), GNSS delay 110 ms, test rules (D-FREEZE-6) |
| FREEZE-7 | S177, 08011e92d0 | D-JFF-KEEP commits 20b4a41b22 and aa4fd2654a, D-OFFB-POSVEL xy gains (Q11 B), XY gains 1.9/3.6 |
| FREEZE-8 | S181, d2f3845292 | setpoint extrapolation F2 9dd5f76382, lead constant F4 0.03 s, `MC_INDI_XY_P` default 1.2 (D-G4-STEPBACK) |
| FREEZE-9 | S183, 83976c5099 | `MC_INDI_XY_VP` default 2.4 (D-XY-PICK) |
| FREEZE-10 | S192, 7fe6206fcc | full revert of aa4fd2654a (Q23 B) plus D-AF-ALIAS (stage decimation aliased the measured acceleration; G3 cause) |

Later firmware commits under FREEZE-10 were behaviour-neutral (D-G7-NUTTX-BUILD S195 `fminf` compile fix, D-G7-F-TEXT
S196 text edits; `indi_flight/STATE.md` "Status"). The S214 simulator fix `f110361a33` is in `src/modules/simulation`,
not controller code (A.6).

## A.3 Decisions reversed or overturned, and owner questions that changed a gate or test

**Reversed or overturned design decisions**

| what | when | why | source |
|---|---|---|---|
| SDF choice for the simulated barometer (A-14) overturned | S29 | gz-sensors 8 `AirPressureSensor::Load` never reads the value set in the SDF | DECISIONS line 177 |
| INDI "T118 stick pilot PASSED" and G3 probe INDI verdicts (S110-S118) voided | S121 | those runs flew the stock rate loop (`MC_RATE_CTL_TYPE 1` missing from base params); runner fixed and guarded | JOURNAL lines 891-896 |
| `MC_INDI_W_MAX` missing from G3 base parameters: all G3 INDI runs were model-only until fixed | S122 | fix 0a49572149 plus `run_validity.py` marking void runs | JOURNAL line 896 |
| D-RATE-LEAD addendum 2 (c), "identification errs high, round ACT_TC up" | overturned S208 | draw 283 (tau 16.5 ms, 10 ms delay) fails item 2 at ACT_TC x1.5 and x2 and passes at x1, meeting the rule's own overturn clause | D-OWNER-Q27 (DECISIONS line 1300), `indi_flight/results/q26_actc_s207` |
| Commit aa4fd2654a (rate feedforward change kept under D-JFF-KEEP at owner request) reverted | S191-S192 | it was the cause of the G5.7 failure (revert probe PASS 3/3, worst 3.61 deg against limit 5) | D-OWNER-Q23, D-FREEZE-10 |
| Freeze-7 G4 chatter decisions re-opened | S179 | 33.3 Hz (offboard lemniscate) and 20-22 Hz (land descent) lines; led to freeze-8 changes | D-G4-STEPBACK |
| Outer xy gain defaults 1.9/3.6 lowered to 1.2/2.4 | S181, S183 | G4 chatter and G2 phase margin remedy | D-FREEZE-8, D-XY-PICK, D-FREEZE-9 |

**Owner questions that changed a gate or a test** (answers recorded in `indi_flight/JOURNAL.md` unless noted)

| Q | session | change |
|---|---|---|
| Q2 | S24, answered S50 | G1.1 gap rule amended to two hole kinds: holes in the simulator, not in the log (JOURNAL line 314) |
| Q3 | S25, answered S50 | G1.6(a) mode-instant wording restated, since 2.5 ms cannot be met without lockstep gz |
| Q4 | S32, answered S50 | G1 frozen with written evidence limits so stage 2 could start; new G1.7 provenance item |
| Q6 | S119 | identification flown by INDI itself in a conservative configuration (answer B) |
| Q8-Q15 | S143-S174, acted S175 | test-defect fixes after the first G5 and G4 tests (D-OWNER-Q8-Q15); individual answers not read, see Unverified |
| Q17, Q18 | S178-S180 | G5.10 stabilized recovery criterion and G4 chatter windows containing touchdown redefined (D-OWNER-Q17-Q18) |
| Q19, Q20 | S183, S184-S187 | G4 chatter check skips 3 s after a mode change, with a PID guard; Q20 fixed which RMS the guard compares; G4 PASSED under it S187 |
| Q21, Q22 | S185-S187 | G5.10 SAT set-up; G3 error box narrowed, attitude P not changed (P 4.7 breaks G2-STEP and outer xy phase margin) |
| Q23 | S189-S191 | revert of aa4fd2654a, FREEZE-10 |
| Q24 | S194, answered S197 | G3 GNSS mismatch range -100..100 ms narrowed to -50..50 ms; draws 08 and 03 reported as shared with PID |
| Q25 | S197 | G5.5 horizontal limit became max(0.5 m, tau_att x v_rms) with tau_att 0.125 s |
| Q26 | S199, answered S207-S208 | after G3 NOT PASSED: re-fly check with drawn ACT_TC first, no firmware change |
| Q27 | S208 | identify ACT_TC first; controller ACT_TC box written from the measured identification error; round-up rule overturned |
| Q28 | S211 | rule A; G3 controller ACT_TC box r in [0.88, 1.02] x tau_mean |
| Q29 | S211 | G3 re-fly of 300 runs fail-fast, critical block first; G6 item 7 = 60 corners only |
| Q30 | S214 | G3 item 3 scored on a written window: hold of at least 20 s, last 10 s, replacing the 3 s stand-in |
| Q31 | S213 | open: route after the second G3 NOT PASSED (A.4) |

## A.4 Gate history

Current states from `indi_flight/GATE_STATUS.tsv`; verdict texts in `indi_flight/GATES.md` (headings quoted).

| gate | first test | verdicts | current |
|---|---|---|---|
| G1 | S19-S24 (Q2 raised S24 after a first failure) | PASSED S84 | PASSED |
| G2 | rate flights S41-S42; formal G2-STEP 9/9 S64 | freeze-7 NOT PASSED S179; freeze-8 NOT PASSED S182; freeze-9 PASSED S184; freeze-10 PASSED S194 (24/24 outer cells, G2-STEP 9/9; 3 limit cells key 2 blocked on agreement only) | PASSED |
| G3 | hook pre-test S112 (INDI half void S121); pre-test seed 173 S173; Q22 S186 | freeze-10 pre-test S194: four draws failed; campaign 300/300 at freeze-10, NOT PASSED S199; re-fly with drawn ACT_TC halted at run 024, NOT PASSED S213 | NOT PASSED |
| G4 | pre-test S168 | freeze-7 NOT PASSED S178 (re-score S180 unchanged); freeze-9 NOT PASSED S184, PASSED under Q20 S187; freeze-10 PASSED S194 (18/18 both keys) | PASSED |
| G5 | tests written S136-S139; freeze re-fly S158 (G5.5 o1-o4/o7 failed, G5.7 later failed at freeze-9) | PASSED at freeze-10 S198; gaps closed S198 (events seeds 2-3, G5.8 3 m/s). Mission and RTL key 1 only; G5.6, G5.11 z and F-8 rows not tested | PASSED |
| G6 | S209 ACT_TC identification grid (0/30 failed) | none | open |
| G7 | S195 | partial: stock zero diff PASS, 0 gain mismatches, astyle clean, flash size measured; ID_OK 0 waits for G6 | open |
| G8 | report drafted S215 onward | none | open |

**G3 is NOT PASSED twice.** First at FREEZE-10 (S199): run 245 (corner C1) diverged in a growing 2 Hz pitch oscillation
and fell, run 264 (corner C3) tilted past 60 deg, and 79 of 297 scored runs failed item 2 on at least one key; PID flew
both draws without loss of control (`indi_flight/GATES.md` "G3 verdict at freeze-10", line 725). Second in the ACT_TC
re-fly (S213): chain C212 halted at run 024 (draw 264, corner C3), INDI loss of control at 60.78 s at speed 4 and
61.03 s at speed 1 with controller ACT_TC 0.0177; the freeze-10 flights of the same plant (ACT_TC 0.033) failed at the
same time, so the failure did not depend on ACT_TC; PID did not lose control (`indi_flight/GATES.md` line 808). Q31 is
open and blocks G3 and G6 (`indi_flight/QUESTIONS.md` line 69). No outcome is stated here.

## A.5 Errata

| id | wrong number or claim | corrected | source |
|---|---|---|---|
| E-1 | Disturbance wrench applied twice: the injector added a second ApplyLinkWrench on top of the one `server.config` already loaded (A-31, found S66, fixed S67, fix fc8905cf90). Stated magnitudes of every disturbance result before the fix were half of what was flown. | Archive T6 gust_x, T7 payload_add, H2 gust_diag, H3 com_shift and `indi_flight/results/g15_dist_s66/` stand as history only. rpm^2 ratio for the 25 % payload 1.497 became 1.249 (expected 1.2497, second key 1.2490). | `indi_flight/results/errata.md` E-1; `indi_flight/results/a31_fix_s67/README.md`, `second_key.md` |
| archive-1 | Trajectory error scored against a 5 Hz logged reference held between samples (`bench/metrics.py:309-317`). Reported O1 lemniscate ratio INDI/PID 0.69. | Real ratio 0.23 with an interpolated reference, 0.33 with ground truth. Other rows (INDI/PID, ZOH, interpolated): O2 0.72 to 0.17, O3 0.68 to 0.26, O4 0.28 to 0.28, O5 0.49 to 0.40, O7 0.70 to 0.23; O6 0.96 to 0.99. | `indi_project/review/external_review_s59.md` sec. 2.1 table; `indi_flight/LESSONS.md` lesson 1 |
| archive-2 | O6 "significantly better, 4 %, p = 0.010" | An artefact: three quarters of both numbers was the held reference. | same, sec. 2.1 consequences |
| archive-3 | Archive sessions 54-55 puzzle "INDI POS runs ahead of the reference" and part of the GNSS-delay investigation | Chased the held-reference artefact; the GNSS-delay finding itself was real. | same, sec. 2.1 |
| archive-4 | Report 8.10 mislabelled V' rows (W3 and W5 swapped; no entry had an eRPM gain error) | Labels exchanged. | same, sec. 2.3 |
| archive-5 | "1 kHz gyro" (10.5, 7.7) | The IMU ran at 1 kHz but `IMU_GYRO_RATEMAX` 800 gave a 500 Hz rate loop; INDI POS and its attitude loop 125 Hz. | same, sec. 2.3 |
| archive-6 | Hover-effort criterion that failed stages 2b and 8 | It measured 0.1 % of full-scale command, noise-sized in the simulator; says nothing about hardware. | same, sec. 2.2 |
| this-1 | INDI verdicts of T118, P117 and the G3 ladder (S110-S118) | Void: the runs flew the stock rate loop; re-flown after S121. | `indi_flight/JOURNAL.md` line 891 |
| this-2 | G3 INDI runs before S122 | Model-only because `MC_INDI_W_MAX` was missing; void runs identified by `run_validity.py`. | `indi_flight/JOURNAL.md` line 896 |
| this-3 | G3 pre-S214 C3 (saturation hook plus weak motor) runs | Failed GATES validity 2: the multi-motor fault was applied split by 1 s (A.6). The draw-264 loss of control was re-flown with the fix and remained. | `indi_flight/JOURNAL.md` line 1913 |
| this-4 | S214 note "ITEM3_DECOMP gust-timing line" | Corrected in `Q30_REVIEW.md`: the gust ended about 5 s before the window and the line mixed time bases. | `indi_flight/JOURNAL.md` line 1903 |

## A.6 Simulator and tooling defects found

| defect | found, fixed | source |
|---|---|---|
| Disturbance wrench applied twice (injector plus `server.config`) | S66, S67 fc8905cf90 | `indi_flight/results/errata.md` E-1 |
| Held 5 Hz reference in `bench/metrics.py` (archive) | review after S59 | `indi_project/review/external_review_s59.md` sec. 2.1 |
| Barometer SDF value never read by gz-sensors 8 | S29 | `indi_flight/DECISIONS.md` line 177 |
| `margins_est` least-squares phasor DC-term defect | S85, fixed | `indi_flight/JOURNAL.md` line 715 |
| G3 hook pre-test: wind not air-relative (gz Pose message class missing), inertia draws invalid about 1/3, eRPM loss started late (set_param latency) | S112 | `indi_flight/JOURNAL.md` line 827 |
| G3 base params missing `MC_RATE_CTL_TYPE 1` (stock rate loop flown) and `MC_INDI_W_MAX` | S121, S122 | `indi_flight/JOURNAL.md` lines 891, 896 |
| G5 injector: ekf_yaw sent id 43002 instead of 620; `rcS` scaled `COM_RC_LOSS_T` by speed factor; MAVLink events 3-24 ms late | S143-S144 | `indi_flight/JOURNAL.md` lines 960, 962 |
| A-48: eight sequential per-motor EC_MAX sets at the G5.10 saturation release were an injector artefact; uniform faults moved to atomic `SIM_GZ_THR_SC` | S148, 867e10424a | `indi_flight/JOURNAL.md` line 967 |
| G3 checker defects: excursion measured against the 5 m lemniscate instead of the time-matched setpoint; G4 chatter line wrongly decided G3 item 2 | S186 | `indi_flight/JOURNAL.md` line 1428 |
| NuttX compile failure of `mc_indi_pos_control` (`std::fmin`) | S195, e9e85e395d (fminf) | `indi_flight/JOURNAL.md` line 1526 |
| GZBridge applied parameter updates at a 1 s interval, splitting multi-motor EC_MAX writes 1 s apart | S214, f110361a33 (stock file, owner allowed) | `indi_flight/JOURNAL.md` line 1913; `indi_flight/results/q31_injector_fix_s214/README.md` |
| Harness artefact: LAND overridden by stick re-centre, draw 039 | S199 | `indi_flight/GATES.md` line 725 block |

## Unverified

- Freeze numbers 1 to 5 were not found; the first recorded freeze is D-FREEZE-6 (stage-6 freeze). Whether earlier
  numbering existed was not checked.
- Exact first session of stages 5, 6 and 7 as defined by the journal was not found by keyword; the ranges in A.2 come
  from the dated entries cited, and stage 1 and 2 ends from JOURNAL lines 184-185 only.
- Q8-Q15, Q17, Q18 and Q21 individual answers were not read; only their decision headings (D-OWNER-Q8-Q15,
  D-OWNER-Q17-Q18) are cited.
- `indi_flight/LESSONS.md` lesson 1 labels the 5 Hz metric defect "Stage 1"; the review places it in the archive's
  `bench/metrics.py` (stage 8 trajectory metric). The archive-1 row follows the review.
- `indi_flight/results/errata.md` E-1 itself marks the x500 scope (T6, T7, H2, H3) as UNVERIFIED against the archived
  run log. Only E-1 exists in that file.
- Whether this project re-scored any archive result with the corrected metric was not checked.
- G1 first-test session (S19-S24) is inferred from JOURNAL lines 73-75 and Q2 (S24).
- Q31 outcome is not known and not stated.
