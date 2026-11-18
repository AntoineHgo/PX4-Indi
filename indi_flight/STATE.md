# STATE (budget 8000 bytes: read at every launch, resume essentials only)

## Status
- Stage: 3 (inner loop) opened S49; stage 2 (analysis tools, margins) from S36, provisional under Q4-A; stage 1 frozen S36 (G1 FINAL). Started S1 (2026-11-15). Stage 0 done. Session 3: ref airframe model done.
- Gates: G1 open | G2 open | G3 open | G4 open | G5 open | G6 open | G7 open | G8 open. G1 FROZEN with evidence limits (GATES.md G1 FINAL), not passed until Q2-Q4 answered.
- Blocker: none. S50: owner answered Q2 (A amended), Q3 (A), Q4 (A + G1.7 provenance); GATES.md updated, provisional mark lifted; QUESTIONS.md empty. Q1 closed: A confirmed by owner; flatness A18 reviewed (r5 BLOCKING), answered in
  `design/flatness_r2.md` (S15): optional increment after base A. Outer-loop study finished; stage 5 = base A.
- S36: G1 FINAL written in GATES.md (frozen with 5 evidence limits, provisional under Q4-A, not marked passed);
  stage 2 started provisionally; opus review T73 r1 BLOCKING (gyro break misses INDI's model and rotor-speed
  paths) answered by D-G2-BREAK (M3a torque-setpoint break) and note section 7; r2 CLOSED.
## Next actions (in order)
S44-S67 history: JOURNAL.md. Agent ledger: LEDGER.md. Lessons proposed: LESSONS_PROPOSED.md (agent cost calibrations: read before sizing a brief).
NEXT (S65), per route check 64 (inner loop time-boxed: 1 session per law change from now on):
   (1) stage-5 slice 2: thrust-gap hover in position mode (NEW scenario, N1 C3; MC_INDI_W_MAX 2700) + one
   velocity/acceleration mode (altitude or position stick) + T123 deviations A3/A5/reset; haiku second key.
   (2) Bench defect N1 C2 (disturbance.py payload_add/com_shift/gust sized for x500): take mass/drag from the flown
   model, G1.5 check per profile. (3) Check the 'NOT FOUND' hooks of the draft (loop delay, GNSS latency, vibration)
   against stage-1 sim work before building. (4) G2-STEP 400 Hz reported run DONE S64 (9/9 within limits, A-30 seed spread parked).
   (5) attitude-break margin with the new setpoint path (G2) when the G2 table is resumed.
   Later: G5 build order (draft end), combined opus review of stage-3 safety diff + stage-5 slice before any freeze.
   S65-S68 session notes: JOURNAL.md (S69 entry).
   S69-S71: JOURNAL.md. Route checks 64, 69 in design/. Route check 74 done; next: S79.
   S72 (launch 20261118-003830, cap $3): D-GAP implemented and committed (3481bdcf9e, 41d44d461a; reset() model path
   at u + b, fixed by me after reading the diff). gap085_indi_htoff dz 0.025 m PASS, loss08_indi 0.056 m marginal;
   second key agrees (`results/stage5_s72/second_key.md`). A-33 OPEN: loss08 holds a_c-a_f = 0.158 m/s2 (control
   error 0.040 m), blend should be integral at DC. Closing flight loss08_indi_htoff: HTE ruled out.
   S73: A-33 CLOSED (results/stage5_s73/README.md): rate blend MC_INDI_ACT_BLD default 0 = no integral action;
   blend 0.3/1.0 removes the 10.4 deg standing error. D-RATE-BLD PROPOSED (default 1.0 s, 3 preconditions).
   S74 (launch 20261118-010057, cap $1.51): route check 74 done (design/route_check_74.md, accepted with one change:
   the default change waits for the margins, lesson 10). Root cause of recent work: decision 2 (every measured-state
   loop needs its own integral path). Rule: no new anomaly chase unless a gate test fails; cap one session each.
   S75 (launch 20261118-010441, cap $1.16, no agent): edge semantics DECIDED, no firmware change (D-RATE-BLD-EDGE:
   rate blend snaps to instantaneous gap = correct for a complementary filter; D-GAP keeps freeze).
   S76: rate M3a 800 Hz at tb 1.0/0.3/0.1 flown. S77 (cap $2.91): unit tests done (499e1df991), A-34 traced (open).
   S78 (cap $1.98, below the $2 needed for (b)): did (c) by model + second key. NEXT S79: route check 79 first.
   NEXT S78: (a) DONE S77 (400 Hz margins, rate precondition 1 met at 400/800); (b) D-GAP
   velocity-break PM at tb, tb/3: NO outer-loop injector exists (`results/stage3_s77_400/velbreak_search.md`):
   sonnet task (~$0.9) = injector at the accel/collective setpoint in mc_indi_pos_control mirroring D-G2-INJ
   (MC_INDI_POS_INJ_*, log c/d/u) + csv script, then haiku second key; brief it at a cap >= $2. Then D-RATE-BLD
   accept + firmware default MC_INDI_ACT_BLD 1.0 in its own commit (flights keep setting 1.0 meanwhile);
   (c) A-34: model route done S78 (shift explained, bins fail on A-35 offset); left = haiku flight at
   da64bc26b3^ (worktree build, S57 file, expect PM 77.5 within 2 deg); A-35 (model 1-8 Hz offset) before G2 freeze;
   (d) runner RC/manual stick-path stub + PVA slice (ZSINE_O6), before land/re-take-off;
   (e) combined opus review (stage-3 safety diff + stage-5 slices + snap-vs-freeze), land/re-take-off flight.
   Guard note: a long inline `git commit -m` with this kind of text was blocked; use `git commit -F <scratch file>`.
## Tasks in flight
| id | task | agent | output | resume |
|---|---|---|---|---|
| T160 | S72 D-GAP impl + unit tests + 2 flights | sonnet | results/stage5_s72/README.md | DONE, committed 3481bdcf9e/41d44d461a |
| T161 | S72 second key | haiku | results/stage5_s72/second_key.md | DONE |
| F72 | loss08_indi_htoff flight | bg shell | results/stage5_s72/loss08_indi_htoff/ | DONE |
| T163 | S74 route check 74 | sonnet | design/route_check_74.md | DONE |
| F76 | S76 D-RATE-BLD roll M3a 800 Hz tb 1.0/0.3/0.1 | bg shell | results/stage3_s76_bld/README.md | DONE: PM 68 deg, GM 16 dB, DM 43-46 ms at every tb (no tb effect); precondition 1 met at 800 Hz. TODO: add A-34 row (PM 68 vs S57 77 deg, f_c 4.1 vs 3.1 Hz, same params; closing test = S57 params at HEAD blend off, else bisect) to ANOMALIES.md and an S76 line under D-RATE-BLD in DECISIONS.md (guard blocked my heredoc) |
| F77 | S77 A-34 closing: S57 params at HEAD tb 0 / 1.0 | bg shell | results/stage3_s77_a34/README.md | DONE: blend and load ruled out, likely setpoint lead da64bc26b3; A-34 open with closing test |
| T164 | S77 D-RATE-BLD unit tests | sonnet | results/stage3_s77_tests/README.md | DONE, 69/69, break-checked, committed 499e1df991 |
| F77b | S77 rate M3a 400 Hz tb 0 / 1.0, sequential | bg shell | results/stage3_s77_400/README.md | DONE: PM 70, GM 13.3 dB, DM 51 ms both tb |
| T166 | S78 A-34 closing by model | sonnet | results/stage3_s78_a34/README.md | DONE: shift reproduced, bins fail -> A-35; second key T167 no BLOCKING (second_key.md), test Tc made literal + break-checked |
| F73 | A-33 closing: loss08 with rate blend MC_INDI_ACT_BLD 0.3 / 1.0 (default 0 = off, never set in S72 flights: lesson-9 gap in the rate loop) | bg shell, instances 0/1 | results/stage5_s73/loss08_bld{0.3,1.0}/ | DONE, A-33 closed |

## Open problems
- Review notes folder (`indi_project/review/external_review_s59_notes/`) not read in full at stage 0 (budget);
  open per item: `sim_review.md` for simulator work, `module_parity.md` for stage 3/5, `test_review.md` for stage 3,
  `ident_review.md` for stage 4, `remetric.py`/`hover.py` for the errata.

- S38 GM jump explained (T80, `results/stage2_s38/gm_jump_check.md`): INDI measured Tb 0 phase grazes -180 deg on a
  plateau 12-27 Hz; at 800 Hz it crosses at 11.9 Hz (21.1 dB), at 400 Hz only at 27 Hz (34.8 dB) though |L| at 11.9 Hz
  is -22 dB. Model GM is phase-shape sensitive there: in S41 compare measured |L| over the plateau, and report GM
  together with the minimum |L|^-1 where phase is within 10 deg of -180 (decide in GATES.md before the first G2 test).
- Unmodelled in margins_models.py (T78 UNVERIFIED list): AlphaFilter coefficient formula, LPF2p coefficients from
  memory, gz/ESC latency 0, measured path = eta x motor state, yaw, attitude loop; 267 Hz analytic only.
