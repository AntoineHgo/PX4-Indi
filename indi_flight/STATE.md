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
   S65 (launch 20261117-192006, cap $1.5): item (3) DONE T131 (`design/g3_hooks_check_s65.md`): loop delay ABSENT;
   vibration PARTIAL (rotor sinusoid only, no wideband IMU scale); GNSS latency PARTIAL (param SENS_GNSS0_DELAY only,
   no sample delay; draft says EKF2_GPS_DELAY: fix GATES text); eRPM latency EXISTS; drop RNG seed FIXED (hpp:131),
   must become per-run. Item (2) CODED T132 (`design/t132_disturbance_c2_s65.md`, self-test OK, re-run S65): profiles
   sized from SDF (quad5in 0.610 kg, payload 25 % W, gust 10 % W); quad5in CdA 0.012 / CoP 0.02 UNVERIFIED; UNKEYED.
   S66 (launch 20261117-231245, cap $3): T133 second key of T132 AGREE (note errata appended). N2-A triage DONE
   (`design/n2a_triage_s66.md`; A-2/A-15 closed, A-5 archive-only, A-1/A-3/A-7 parked, A-4/A-6 open). T134 G1.5
   pre-test 5 profiles (`results/g15_dist_s66/`): airframe line and wrench peaks OK; open: payload_add thrust +50 %
   vs 25 % force, com_shift roll excursion +79 deg at onset+26 s, torque_steps pitch/yaw sign (FLU vs FRD?).
   T136 (`results/g15_dist_s66/investigation.md`): wrench acts 2x on the vehicle (force and torque) and com_shift
   loses it once at +26 s -> A-31 OPEN, blocks every disturbance result. torque_steps pitch/yaw sign explained
   (world ENU = body FLU at spawn yaw; PX4 FRD flips y, z): document in disturbance.py, not a defect.
   T137 read gz-sim 8.15.0 ApplyLinkWrench (`design/a31_wrench_source_s66.md`): one-step msgs summed per step, no
   mechanism for 2x found. NEXT S67: (a) A-31 first: the 4 tests at the end of that note (payload_add alone first); fix + second key + re-run g15_dist_s66/fly.sh; N2-B (A-9 unit test on new module) and N2-C (A-30 identical 400 Hz re-fly,
   share with A-4 speed 1/4 test); then item (1) slice 2; build hooks (loop delay, GNSS sample delay, per-run drop
   seed, IMU noise scale) as one simulator task with second key.
   Results rule (N1 D): commit metrics/run.json/README of every run in the session that produced it. Next route check: S69.
Standing rule (S35): bench param sets carry SENS_BAR_AUTOCAL 0.
   S67 (launch 20261117-232529, cap $3): A-31 lead: `src/modules/simulation/gz_bridge/server.config:14` already
   loads ApplyLinkWrench (default.sdf has no plugins, gz_env.sh sets GZ_SIM_SERVER_CONFIG_PATH); disturbance.py adds a
   2nd instance at runtime -> 2x. DONE: fix fc8905cf90, second key AGREE, A-31 CLOSED, 5 profiles re-flown 1x
   (`results/a31_fix_s67/`), errata.md E-1 created. A-30 re-fly (`results/a30_refly_s67`): identical runs DIFFER
   -> Q5 open (non-blocking, rec. G1.6 protocol on INDI). A-9: no path in new module by reading
   (`design/a9_new_module_s67.md`); module publishes no jerk ff (omega_ff unused): trajectory lag, stage-5 item.
   T143 (`results/g16_indi_s67`): INDI 400 Hz same-seed spread rise 4 / settle 15 ms / OS 0.7 pts, equal at speed
   1 and 4; arm instant varies 0.76 s (wall clock); S64 seed1 outside all 11 runs (Q5 addendum).
   T144 log diff: params identical, S64 binary from a DIRTY tree (f183dad) = leading cause of the outlier.
   NEXT S68: (a) Q5/A-30: clean-build re-fly S64 800 Hz seed 1 (+ same-seed batch at 800 Hz) vs
   `results/g2_step_s64`; if it differs, re-fly the S64 G2-STEP tables; arm in sim time in the runner (2nd key); (b) A-9 second key + guard test; (c) slice 2 (item 1); (d) sim hooks task (loop delay,
   GNSS sample delay, per-run drop seed, IMU noise scale) with second key.
   S68 (launch 20261117-234230, cap $3): T145 clean-HEAD re-fly (`results/g2_clean_s68`): 400 Hz table 9/9, seed1 roll
   rise 192.5 (dirty tree not needed as cause); 800 Hz same-seed spread 14.5/39 ms/1 pt, < 1/2 limit margin; A-30
   bounded, Q5 addendum 3. T146: A-9 CLOSED (2nd key AGREE, guard gtest break-checked, 35b313d2a5).
   NEXT S69: route check 69 first; T147 second key + re-measure same-seed spread with sim-time arm; then (c) slice 2, (d) hooks.
## Tasks in flight
| id | task | agent | output | resume |
|---|---|---|---|---|
| T148 | A-30 discriminator, --sched, 400 Hz seed 1 x5 each: PID / INDI v2true / INDI all-eRPM-lost (T147 done: sched spread 6/15 ms rise) | haiku | `results/a30_disc_s68/README.md` | `bash results/a30_disc_s68/fly.sh` |

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
