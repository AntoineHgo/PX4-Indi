# STATE (budget 8000 bytes: read at every launch, resume essentials only)

## Status
- Stage: 3 (inner loop) opened S49; stage 2 (analysis tools, margins) from S36; stage 1 frozen S36 (G1 FINAL). Started S1 (2026-11-15). Stage 0 done. Session 3: ref airframe model done.
- Gates: G1 PASSED S84 (owner S50 rule; G1.5 per injector, evidence limits) | G2 open (cell table in GATES.md) | G3 open | G4 open | G5 open | G6 open | G7 open | G8 open.
- Blocker: none. QUESTIONS.md empty (Q1-Q5, N1, N2 closed). Outer-loop study finished; stage 5 = base A
  (`design/flatness_r2.md`: flatness = optional increment after base A).
## Next actions (in order)
History: JOURNAL.md (S107 entry holds the latest moves). Agent ledger: LEDGER.md. Lessons proposed:
LESSONS_PROPOSED.md (agent cost calibrations: read before sizing a brief). Route checks in design/; next: S113.
Rule (RC64/RC74): inner loop time-boxed, 1 session per law change; no new anomaly chase unless a gate test fails.
NEXT S108 per RC108 (design/route_check_108.md, filed S107; next route check S113). Accepted with one amendment:
   G3/G5 batches before the stage-6 freeze are PROBES of the current stack (find failures early), not gate evidence.
   S108 DONE 93f94320d3: design/g2_verdict_s108.md + GATES.md G2 table (outer cells S83/S86/S87 added; draft had
     missed them). Attitude seed 2 NOT flown (pre-freeze, stage 6 re-flies all). Offline G2 todo before stage 6:
     outer-cell margin key, linear outer-loop model, A-36/A-39 bound, 267 Hz rows.
   S109 order: close K108 findings; quad5in model variants (tau, asym, mass, inertia; lift x500-only abort) +
     frozen-telemetry hook (two keys, G1.5 check); g3_checks.py + key; gate_g3.sh consuming the run JSON hooks block.
   S109: G3 randomised runner (plant draw per run, all G3 axes incl. GNSS hook B: matched = --gnss-delay == --gps-dly)
     + ~20-run pre-test; fold G1.5 estimator M-vs-X separation (moving scenario) into it.
   S110: first G3 probe batch >= 60 runs. S111: G5 mode/transition batch. S112: G4 noise profiles.
   STOP: A-39 / yaw measured-path chase, more G2 cells at the preliminary pair, PID M1 hook, hooks without a consumer,
     stand-alone anomaly chases (fold A-4, A-6 into G3/G5 side-cells).
   Done history (RC103 list i-vi, hooks A1/A2/B, A-37, A-38, yaw model): JOURNAL.md S101-S107.
   Later: G5 build order (draft end), combined opus review of stage-3 safety diff + stage-5 slice before any freeze.
   Old: log a z-only active flag in indi_pos_status when next touching the module (P98 could not see it).
Notes: pretest_gate only on stationary scenarios, or end its window at the fault (S98). S99 hooks SIM_GZ_SEED +
   SIM_GZ_IMU_NSC done (accel scale UNVERIFIED, needs full-rate accel log before G4). D-G7-HARNESS decided, impl
   stage 7. M3 PT-change UNVERIFIED. Deferred anomalies: A-4, A-6, A-30, A-32, A-34-A-36, A-39. PID M1 hook deferred (RC103).
   Flights no longer need MC_INDI_ACT_BLD 1.0 (default). Check script bench/attitude_break_check.py; ratesp_csv.py keyed.
   Guard note: a long inline `git commit -m` was blocked; use `git commit -F <scratch file>`.
## Tasks in flight
| id | task | agent | output | resume |
|---|---|---|---|---|
(Done rows up to K101/B100: JOURNAL.md S100/S101 entries.)
| H102 | S102: delay-line hooks A1+A2 in gz_bridge (uncommitted, builds, 0 warnings, not flown) | sonnet | design/delay_line_impl_s102.md | DONE; orchestrator read diff, OK |
| K102 | S102: second key of H102 | sonnet | design/delay_line_key_s102.md | DONE: 0 BLOCKING, M1+M2 fixed by orchestrator, c6ba02609f |
| V102 | S102: delay-hook pre-test d0/d5 | haiku | results/delay_pretest_s102/README.md | DONE: IMU PASS (age 0/5000 us), actuator UNVERIFIED -> A-37 |
| G104 | S104: scope G2 verdict note (iii), read-only | haiku | design/g2_verdict_scope_s104.md | DONE (haiku, UNVERIFIED): table claim checked: results/g2_rate_table_s99.md "S101 update" holds 24/24 (K100+K101), only its body is pre-S101; A-21 model-vs-measured PM gap ~18 deg (results/stage2_s41/a21_model_vs_measured.md) > 10 deg G2 tolerance: check which loop/version it was before (iii) |
| X105 | S105: G2 model-vs-measured cross-check, offline | sonnet | design/g2_crosscheck_s105.md | DONE: 16 roll/pitch cells within tol (dPM<=4.7, dGM<=1.86); yaw unmodelled; filters verified; A-21 n/a to v2 |
| RC103 | S103: route check | sonnet | design/route_check_103.md | DONE: A-37 time-box $0.5 then park; then G5 pre-tests, G2 verdict note, hook B; defer PID M1 |
| S103 | S103: scope POSCTL stick gap scenario (read-only) | haiku | design/posctl_gap_scope_s103.md | DONE: scenario + --stick-mode posctl, flown |
| H106 | S106: hook B GNSS delay (SIM_GZ_GPS_DLY) impl+build+1 flight | sonnet | design/gnss_delay_impl_s106.md | DONE d52576b02a (fw) bd0aa768f4 (pretest: age 200000 us x110, 1 Hz log) |
| K106 | S106: second key of H106 + L=250 flights | sonnet | results/gnss_delay_key_s106/README.md | DONE: BLOCKING (SENS_GNSS0_DELAY inert) fixed 99673b62bd, M2 verified (EKF time err +4 ms matched) |
| K107 | S106: second key of fix 99673b62bd (read-only) | sonnet | design/gnss_delay_fix_key_s106.md | DONE: no BLOCKING; MINOR overflow releases not in age0 range (accepted, overflow counted); astyle clean |
| Y107 | S107: yaw linear model in margins_models.py + 8 yaw cells cross-check (offline) | sonnet | design/g2_yaw_crosscheck_s107.md | DONE (Y107b, 2nd key of model: law VERIFIED, 0 BLOCKING): model-only 4/4 in tol; measured 1/4 in tol -> A-39. margins_of hangs if ts_true=0 (tool defect, open) |
| B107 | S107: attitude-break cells (vi) at HEAD, pretest 1 cell then 5 | sonnet | results/g2_attbreak_s107/README.md | DONE 8ec7d4a95b: 6/6 PASS (PM>=56.8, GM>=22 dB, DM>=0.118 s), dPM<=0.5 vs S91 |
| D107 | S107: DRAFT G2 verdict update (rate+yaw+attitude) for S108 review; does not edit GATES.md | sonnet | design/g2_verdict_s108_draft.md | DONE draft (10 UNVERIFIED). S108: review, then GATES.md. Gate asks worst of 2 runs: attitude S107 cells are 1 seed -> fly seed 2 (6 flights) |
| G108 | S108: G3 sampler bench/g3_sample.py + self-test + factor->hook map (no flight) | sonnet | design/g3_sampler_s108.md | DONE 238079b24f: 9/9 self-test, deterministic (orchestrator re-ran); hooks 8 exist / 6 partial / 6 missing (tau, asym, mass, inertia on quad5in: run_scenario.py:203 x500-only; frozen telemetry; G4 profile). D-G3-SAMPLER |
| K108 | S108: second key of g3_sample.py vs GATES G3 spec (read-only) | sonnet | design/g3_sampler_key_s108.md | DONE: 0 BLOCKING, 4 MAJOR, 8 MINOR (key read author note early: partial independence). S109 fix: G1 error as controller/plant ratio incl. drawn inertia (now 0.35-2.6, out of x[0.5,2]); gust present whenever drawn (C4 needs a gust); add tests for surviving mutations; saturation share kept per D-G3-SAMPLER |
| A103 | S103: A-37 test (a9e5066a55), hover d5/d10 | host bg | results/a37_actlag_s103/README.md | DONE: A-37 closed |
S102 finding: (ii) PID M1 has NO recipe: the gyro-break hook (`sim_inject`, design/stage2_margins_s35.md l.21) was never built.
  PID reference is F-5 reference only -> deferred behind (iv); build the M1 hook later in gz_bridge IMU callback beside A2.

## Open problems
- Deferred to stage 7 (RC98): module harness (D-G7-HARNESS), MINORs frozen-b on saturated motor, lagging
  mean_u at reset, lower mean_u limit untested, DESCEND failsafe tests (T202/T205 rows in JOURNAL S98).
- Review notes folder (`indi_project/review/external_review_s59_notes/`) not read in full at stage 0 (budget);
  open per item: `sim_review.md` for simulator work, `module_parity.md` for stage 3/5, `test_review.md` for stage 3,
  `ident_review.md` for stage 4, `remetric.py`/`hover.py` for the errata.
- Unmodelled in margins_models.py (T78 UNVERIFIED list; filters verified S105): gz/ESC latency 0 (likely cause of
  1-2 dB 400 Hz GM residual), measured path = eta x motor state, yaw, attitude loop; 267 Hz analytic only.
