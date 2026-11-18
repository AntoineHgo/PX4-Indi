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
   S82 (launch 20261118-042344, cap $3): T169 stick stub DONE (a1f2b3b124, 53b38dd54e; results/stage5_s81_stick/
   README.md): altctl/posctl fly on both stacks, 50 Hz grid pacing; PID = INDI gain 0.86 (stock setpoint shaping).
   T170 DONE (3b7af1282f fw, 37f3ab90a5, 9278260a9d): MC_INDI_PINJ_* injects at the INDI stage INPUT = velocity/
   position break (INDI accel loop closed), z PM 54.4 deg at 0.60 Hz, tb 1.0, pre-test only (results/stage5_s82_
   velbreak/README.md lists open items). The G2 accel-loop break (d at stage output) is still missing.
   NEXT S83 (cheap first): (1) haiku second keys: stick stub (to brief_rc_stub_s80.md) and injector (to
   brief_velbreak_s82.md); (2) re-fly velbreak with DLY >= 15 s / NP 5 at tb 1.0 and tb/3 (D-GAP overturn test);
   (3) G5 stick metric vs vehicle_local_position_setpoint; then (e) or PVA slice.
   S83 (launch 20261118-043259, cap $3): injector second key AGREE WITH MINOR, minors fixed (a38533428f fw,
   907f57510d pinj_csv self-test); velbreak re-fly z PM 57.3 (tb 1.0) / 59.1 deg (tb 0.33): D-GAP PM overturn NOT
   met (cdc5f03713); stick second key DISAGREE (33 Hz rows pre-grid, README overclaim) -> 4 rows re-flown (B83b).
   S84: RC84 done (design/route_check_84.md), G1 PASSED, G2 cell table in GATES.md, T174 launched.
   S84 HF output-break re-fly (1.5-10 Hz): abs(L) <= -10 dB, no -180 crossing (UNKEYED, results/stage5_s84_accbreak/
   README.md); pinj_csv --margins raises when no crossover in band (fix).
   NEXT S85 (RC84 plan): (1) haiku/sonnet second key of hf_frf.txt with margins_est coherence + pinj_csv fix; AX=0 identity flight;
   (2) per-run hole reporter (extend bench/a15_gaps.py, self-test); (3) fly remaining G2 outer cells with one runner
   (xy velbreak, accel break z/xy at 800/400); (4) attitude-break design note. S86: G2 report + G5 text; then (e)
   combined opus review. Deferred anomalies: A-4, A-6, A-30, A-32, A-34, A-35. Next route check S89.
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
