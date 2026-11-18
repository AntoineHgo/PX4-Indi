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
   NEXT S87: (1) hole_report count check: disagreement of 1 flagged FAIL (spec > 1) and actuator_motors differs by 3 at
   800 Hz on healthy runs -> fix + test (sonnet), re-run on all s86 cells; (2) summarise seed-2 z cells (zbatch.log);
   (3) second key of T181 (haiku: recompute xy FRF from the CSVs), rename top_db, re-fly xy cells serially with
   AMP 0.08 TP 20 (pt0/pt1 x ax1,2 x 400/800 x 2 seeds); (4) review attitude-break note (sonnet, one interface: note vs
   code), then implement; then G2 report + G5 text; then (e) combined opus review. Deferred anomalies: A-4, A-6, A-30, A-32, A-34, A-35. Next route check S89.
   Guard note: a long inline `git commit -m` with this kind of text was blocked; use `git commit -F <scratch file>`.
## Tasks in flight
| id | task | agent | output | resume |
|---|---|---|---|---|
(S72-S78 rows done, details in JOURNAL.md; A-34/A-35 rows and S76 D-RATE-BLD line are recorded.)
| B83 | velbreak re-fly TB 1.0/0.33 | host | results/stage5_s83_velbreak/README.md | DONE cdc5f03713, PM 57.3/59.1 deg |
| T173 | injector minors + pinj_csv self-test | sonnet | results/stage5_s83_velbreak/minors_fix.md | DONE a38533428f, 907f57510d |
| B83b | stick re-fly x4, grid pacing | host | results/stage5_s83_stick/README.md | DONE: all 50 Hz, gain 0.86 both stacks; open: sched anchor for stick mode (G5) |
| RC84 | S84 route check | sonnet | design/route_check_84.md | DONE: G1 bookkeeping (done), G2 cell table (done), then T174 |
| T174 | accel-loop break at stage output (MC_INDI_PINJ_PT) | sonnet | results/stage5_s84_accbreak/README.md | DONE 20b1c9c48b fw, 292b71c333 tool; z pre-test PM 58.7 deg 0.62 Hz; HF bins incoherent |
| T175 | second key of T174, code vs brief | sonnet | results/stage5_s84_accbreak/second_key.md | DONE AGREE WITH MINOR; param texts fixed, rest accepted (README) |
| T176 | S85 HF FRF second key + pinj_csv no-crossover fix | sonnet | results/stage5_s84_accbreak/hf_second_key.md | DONE AGREE, 5444196ab4 |
| T177 | S85 per-run hole reporter + self-test | sonnet | bench/hole_report.py, results/stage5_s85_holes/README.md | DONE 35024c732e |
| T178 | S85 second key of hole_report | sonnet | results/stage5_s85_holes/second_key.md | DONE AGREE WITH MINOR, recount exact; fixes queued S86 |
| T179 | S86 hole_report fixes (findings 1-3) + break tests | sonnet | results/stage5_s85_holes/fixes_s86.md | DONE 98e977a9f0; S83/S84 single flights still PASS |
| T180 | attitude-break note | sonnet | design/attitude_break_s86.md | DONE edc562526a, unreviewed |
| T181 | xy no-crossover diagnosis | sonnet | results/stage5_s86_g2outer/t181_xy_diagnosis.md | DONE: top_db misread; UNKEYED |
| B86z | z cells serial: s1 done; s2 + pt0_ax3_r400_s2 may still run at session end | host | results/stage5_s86_g2outer/zbatch.log | resume: `bash fly.sh PT 3 RATE 2` for any cell without _holes.txt; commit metrics |
| B86 | G2 outer cells: pre-test pt0ax1r400, pt1ax1r400, pt1ax3r800 seed 1 | host | results/stage5_s86_g2outer/ (fly.sh PT AX RATE SEED) | in flight; resume: re-run fly.sh per missing cell |

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
