# STATE (budget 8000 bytes: read at every launch, resume essentials only)

## Status
- Stage: 6 (validation). FREEZE-10 (D-FREEZE-10): firmware 7fe6206fcc, config g5_freeze_s157 params (XY gains at
  firmware defaults 1.2/2.4). Later commits e9e85e395d, 39c1700523 behaviour-neutral (D-G7-NUTTX-BUILD); gate binary
  built 22:38 after 7fe6206fcc, not rebuilt.
- Gates: see GATE_STATUS.tsv. G1, G2, G4, G5 PASSED; G3 NOT PASSED at freeze-10 (S199), Q26 open.
- G3 tooling: flight chain `bench/g3_chain.sh` (README in results/g3_campaign_f10; speed-1 rule in its
  speed_check/README.md); list re-fly with PID twins: results/g3_refly_s199/refly_all.sh.
- Owner answers Q24 B and Q25 B (2026-11-22) acted on S197: GATES "Owner amendments S197", D-OWNER-Q24, D-OWNER-Q25,
  design/airframe_requirements.md (F-3 list + bring-up items). FREEZE-10 stands.
- Owner rule F-10 (2026-11-22): delivered code short needed comments, no project ids/paths, explicit names, PX4
  style. Brief every coder with F-10. Clean-up = separate behaviour-neutral commits, independent review.

## Next actions (each names its gate item)
1. G3 NOT PASSED at freeze-10 (S199, GATES "G3 verdict at freeze-10"; FAILS_S199.md, g3_refly_s199/SUMMARY.md).
   Q26 open (A: cause search then FREEZE-11 with G2/G4/G5/G3 re-fly; B: close as limit). Meanwhile, the one-session
   cause search (needed under A and B): 245 (C1 2 Hz pitch divergence), 239 (class B 2 Hz), 283 (class A 10.75 Hz q),
   264 (C3 saturation + weak motor tilt). Raw ulg in g3_campaign_f10/run_NNN and g3_refly_s199/indi_NNN, PID twins in
   g3_refly_s199/pid_NNN. Suspects: fixed ACT_TC vs drawn tau (slow/asymmetric), delay absent from the modelled
   state, rate gain with controller G1 below plant at high delay (margins measured only at nominal plant), allocation
   under saturation with a weak motor. First pass done (g3_refly_s199/CAUSE_S199.md): rate-loop phase margin with
   drawn tau x3 (245/239) or x0.5 + delay (283), saturation after growth; 264 weak-motor yaw collapse, PID recovers.
   Linear model done S200 (MARGINS_S200.md): 245/239 = rate+attitude cascade at tau x3, PM 6/13 deg (shown); 283 GM
   gap outside model; no fixed ACT_TC covers the box (best 0.05, worst PM 15 deg). Q26 addendum: option C (tau box =
   identification error) + A for 264 only. Cause search closed; wait for Q26, no firmware change before it. Side
   defect: key 1 (g3_score.sh) scores landing windows that key 2 skips (class C, 25 runs).
   Pre-test 17/20 (results/g3_pretest_q24_s197). 02 item-3 miss (0.318 m, +48 ms) is a quota item, not a chase.
2. G5 PASSED at freeze-10 (S198). A firmware change after the freeze re-opens the rows it touches (freeze rule).
   Trap: key2 rows script writes results/g5_events_s145/key2_rows.md (fixed path): `git checkout` it after use.
3. G7 open items: (f) F-10 clean-up per results/g7_s198/F10_PLAN.md, D-F10-NEUTRAL; unit 1 done S200 (ef748da3ce,
   F10_UNIT1.md: separate build dir build/f10_sitl, objdump identical; two "INDI stage" log strings left). Next unit 2
   (re-use the unit 1 brief). One unit per session, never during gate flights; public renames listed, not done.
   (g) build check of indi-fw-pr with the worktree OUTSIDE the repo (re-run make_fw_branch.sh --force-recreate after
   any firmware commit; quad5in model lives in indi_flight/sim, not in the branch). v6x flash overflow 23.5 kB ->
   report/upstream note. Tests build in px4-indi-sim (px4-dev fails protobuf).
   Harness extraction (D-G7-HARNESS, firmware refactor) after the G3/G5 verdicts, with its re-fly named. Older list:
   MC_INDI_ID_OK call site (K128 MAJOR), D-JFF-SOURCE case, D-OFFB-POSVEL wiring test, omega_ff step on offboard
   entry (key2_jffoffb MINOR); checker defects in bench/tests/SELFTEST_G7_S194.md (no verdict, no LOC check in
   offb_vel_check, IndexError on empty topic); g511 yaw p95 subtraction test (g511_check.py:184); g510
   MPC_TILTMAX_AIR log-read branch (g510_check.py:115-119); ACT_TC/W_MAX firmware vs bench (lesson 12); guard params
   (ERPM_TO/FRZ, SP_TO, DT_MAX) unevidenced.
4. G6: before it, yaw fit fix (r regressor + matched grid = probe V3, K126 MAJORs, A-44). ID_OK 0 waits for G6
   (D-G7-DEFAULTS).
5. G8: report and docs/en page (bring-up items in design/airframe_requirements.md).
Rules: 1 session per inner-loop law change; parallel docker streams only for tolerance-insensitive probes, never gate
  evidence, never a docker build during gate flights; G3 evidence for INDI outer loop needs MC_INDI_POS_EN=1. Next RC:
  S209 (RC194 done).
STOP list (+RC194: A-53/A-54/A-58 bound-only, A-50/A-51 model x-check, G5.5 margin): A-39 / yaw measured-path chase,
  PID M1 hook, hooks without a consumer, stand-alone anomaly chases, --sched-anchor and set_param fixes, EdgeState
  design, more PID G5.10 runs.

## Notes
- Nominal plant: matched GNSS --gps-dly 110 --gnss-delay 110. G4 typical noise: --vib-acc 10 --vib-gyr 0
  --imu-noise-scale 4.0 (D-NOISE-PROF).
- G3 tooling: g3_run.py, quad5in variants, overrides/wind/motor_fault/timed eRPM loss. eRPM-loss lateness 36-122 ms:
  take effective time from the log. Weak+sat unflown. Acro G3-unprobed (G5 carries it). altctl/posctl not in MODE_MIX.
- pretest_gate only on stationary scenarios, or end its window at the fault (S98). SIM_GZ_SEED + SIM_GZ_IMU_NSC hooks.
- Stabilized stick centre = HTE; runner thr0 honours HTE valid flag, fallback MPC_THR_HOVER.
- Runner traps: pid_default + params with MC_INDI_EN 1 flies INDI (s148). MC_INDI_EN 1 in a params file does not start
  the module, only MC_RATE_CTL_TYPE 1 does. Pilot sticks kept after LAND -> RC override to POSCTL. margins_of hangs
  if ts_true=0.
- quad5in defaults: bench/params/quad5in_indi_defaults.params (ACT_TC 0.033); ACT_TC 0.033 in 4040; MC_INDI_ID_OK 0
  halves K.
- Guard blocks long `git commit -m`: use `-F <file>`. Guard denies a segment naming indi_project with rm/tee/git
  apply; run each run.sh call alone, redirect only into indi_flight/.
- chatter_cruise_s176.py without RAW= overwrites tracked results/g4_gate_s169/chatter_cruise_s176_raw.txt: brief
  agents to set RAW to their own folder; `git checkout` it if dirty.
- Detached chains: list every waiter pid in Tasks in flight.
- Logger misses the first ~0.2 s of indi_pos_status (late subscription): never read a missing sample as bypass.
- Worktrees and big builds go OUTSIDE the repo (S196 OOM: VS Code indexed an in-repo worktree to 23 GB).

## Tasks in flight
| id | task | agent | output | resume |
|---|---|---|---|---|
| - | none | - | - | - |

## Open problems
- Deferred to stage 7 (RC98): MINORs frozen-b on saturated motor, lagging mean_u at reset, lower mean_u limit
  untested, DESCEND failsafe tests.
- Review notes (`indi_project/review/external_review_s59_notes/`): `module_parity.md` for stage 5.
- Unmodelled in margins_models.py: measured path = eta x motor state, yaw structure (A-51), attitude loop; 267 Hz
  analytic only. Motor latency optional (lat_s, S175).
- Deferred anomalies: A-4, A-6, A-30, A-32, A-34-A-36, A-39.
