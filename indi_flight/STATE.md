# STATE (budget 8000 bytes: read at every launch, resume essentials only)

## Status
- Stage: 3 (inner loop) opened S49; stage 2 (analysis tools, margins) from S36, provisional under Q4-A; stage 1 frozen S36 (G1 FINAL). Started S1 (2026-11-15). Stage 0 done. Session 3: ref airframe model done.
- Gates: G1 PASSED S84 (owner S50 rule; G1.5 per injector, evidence limits) | G2 open (cell table in GATES.md) | G3 open | G4 open | G5 open | G6 open | G7 open | G8 open. G1 FROZEN with evidence limits (GATES.md G1 FINAL), not passed until Q2-Q4 answered.
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
   S69-S71: JOURNAL.md. Route checks 64-79 in design/; next: S84.
   S72-S80 (D-GAP, D-RATE-BLD accepted, A-34/A-35 parked, RC74/RC79): JOURNAL.md. Rule (RC74): no new anomaly
   chase unless a gate test fails, one session cap each. Flights no longer need MC_INDI_ACT_BLD 1.0 (default).
   S82-S85 session notes: JOURNAL.md (moved S86). Guard note: use `git commit -F <scratch file>` for long messages.
   S86 (launch 20261118-050243, cap $3): T179 hole_report fixes DONE 98e977a9f0; G2 outer runner
   results/stage5_s86_g2outer/fly.sh (README: findings 1-3); z cells PM 62.8-63.7 deg; G2 cells fly ONE AT A TIME
   (parallel -> holes); xy no-crossover = top_db misread (T181 UNKEYED); attitude-break note design/attitude_break_s86.md
   (T180, unreviewed; check its L_att identity: L_att = A L_rate/(1+L_rate) expected).
   S87 (launch 20261118-051310): T182 count fix c5b5a897e9 + T184 key AGREE WITH MINOR; T183 key of T181 AGREE;
   xy re-fly B87 (stage5_s87_xy, hover_xlong 150 s, AMP 0.08 TP 20).
   S88 (launch 20261118-053836, cap $1.75): (1)(3) done (T186, T187, D-HOLE-EXCESS); (2) re-fly B88 in flight.
   NEXT S89: close T188 key; record B88 results in s86/s87 READMEs and commit cell metrics; route check 89; then
   (4) act on T185 review of attitude-break note, then implement; then G2 report + G5 text; then combined opus review. Deferred anomalies: A-4, A-6, A-30, A-32, A-34, A-35. Next route check S89.
   Guard note: a long inline `git commit -m` with this kind of text was blocked; use `git commit -F <scratch file>`.
## Tasks in flight
| id | task | agent | output | resume |
|---|---|---|---|---|
(S72-S78 rows done, details in JOURNAL.md; A-34/A-35 rows and S76 D-RATE-BLD line are recorded.)
| T179 | S86 hole_report fixes (findings 1-3) + break tests | sonnet | results/stage5_s85_holes/fixes_s86.md | DONE 98e977a9f0; S83/S84 single flights still PASS |
| T180 | attitude-break note | sonnet | design/attitude_break_s86.md | DONE edc562526a, unreviewed |
| T181 | xy no-crossover diagnosis | sonnet | results/stage5_s86_g2outer/t181_xy_diagnosis.md | DONE: top_db misread; UNKEYED |
| B86z | z cells serial, 8 cells | host | results/stage5_s86_g2outer/README.md | DONE: PM 58.3-66.1 deg; 800 Hz cells fail only the count check |
| B86 | G2 outer cells | host | results/stage5_s86_g2outer/ | DONE (z cells; xy re-fly B87) |
| B87 | xy cells AMP 0.08 TP 20 hover_xlong, serial | host | results/stage5_s87_xy/ (fly.sh PT AX RATE SEED) | DONE 30c012bc7c: 16 cells PM 49.7-64.8, GM 18.2-19.3 dB, f_c 0.27-0.34 Hz; holes 15/16 after re-fly 66589220a9 (pt0_ax2_r400_s1: count check + 89 Hz limit, tool fix S88) |
| T182 | hole_report count-check fix + re-run s86 cells | sonnet | results/stage5_s85_holes/count_fix_s87.md | DONE c5b5a897e9 (unkeyed). S86 README rows for r800_s2 were wrong: real holes (pt1 sim 12.5 ms -> re-fly; pt0 only outer topic 89 Hz max 18.75 ms vs 10 ms limit = spec defect for a topic with period > 10 ms?) |
| T184 | second key of T182 (code vs spec) | haiku | results/stage5_s85_holes/second_key_s87.md | DONE c9cc245a40 AGREE WITH MINOR |
| T185 | review attitude-break note vs code | sonnet | design/attitude_break_s86_review.md | DONE: 0 BLOCKING, 2 MAJOR (add call-site test at McIndiRateControl.cpp:231; replace circular x-y-d check by logged rate_sp_dot vs derivative of logged x), 10 MINOR (gate off in ACRO; use hover_xlong; outer loop closed below ~0.3 Hz). Amend note, then implement |
| T186 | S88 hole_report raw-gap + excess limit (D-HOLE-EXCESS) | sonnet | results/stage5_s85_holes/fixes_s88.md | DONE dd9dd0705e: s86 pt0_ax3_r800_s2 FAIL->PASS, 27 unchanged |
| T187 | rename top_db -> last_bin_db | haiku | margins_est.py | DONE 5243e845b9 (README rewrite reverted, kept S87 one) |
| T188 | second key of T186 (code vs spec) | haiku | results/stage5_s85_holes/second_key_s88.md | DONE: AGREE WITH MINOR; slow-topic escape fixed 688f198ab2 (test S88d). Open minors: max_excess under-reported below 1.5x median (report only); median-0 topic -> OverflowError at hole_report.py:58 (loud). S89: re-run hole_report on 28 cells (host idle, no flight running) |
| B88 | re-fly s86 pt1_ax3_r800_s2 then s87 pt0_ax2_r400_s1 (old outputs in holes_fail_s87/) | host | results/stage5_s87_xy/refly_s88.log | S88 launched; if cut: re-run both fly.sh lines serially, check *_holes.txt OVERALL |
| T183 | second key of T181 (xy FRF from CSVs) | haiku | results/stage5_s86_g2outer/t183_second_key.md | DONE d2b66bf3ae: AGREE |L|, PM 54-56; f_c 0.27-0.33 Hz |

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
