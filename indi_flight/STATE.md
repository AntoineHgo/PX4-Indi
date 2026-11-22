# STATE (budget 8000 bytes: read at every launch, resume essentials only)

## Status
- Stage: 6 (validation). FREEZE-10 declared S192 (D-FREEZE-10): firmware 7fe6206fcc (Q23 revert + D-AF-ALIAS),
  config g5_freeze_s157 params (XY gains at firmware defaults 1.2/2.4). Re-fly list in D-FREEZE-10: G2 outer, G4,
  G5 outer rows, G3 pre-test. Probe evidence results/freeze10_cand_s191/README.md (all probe checks PASS).
- Gates: see GATE_STATUS.tsv. Owner answers Q8-Q15 acted on S175 (GATES "Owner amendments S175", D-OWNER-Q8-Q15).
- Blocker: Q24 (S194) blocks G3, Q25 (S194) blocks G5; G7 harness is free work. Q23 closed S191 (D-OWNER-Q23): revert aa4fd2654a (G5.7 cause D-G57-FF); with
  D-AF-ALIAS (G3 7 Hz, outer a_f aliased by 88.9 Hz stage decimation) it enters FREEZE-10.
## Next actions (owner order; each names its gate item)
0. FREEZE-10 re-fly RUNNING (Tasks Q10). RC194 done (design/route_check_194.md): no probes/chases while it runs;
   read queue_status.tsv; a haiku agent collects scores per gate; untested in the queue: g4_score.sh rewrites +
   Q20 guard, abort path -> fix and resume with `queue.sh N` if failed (pyulog on host checked S194). Then
   verdicts. Queue ENDED 01:14 S194. G4 PASSED at freeze-10 (S194). G3 pre-test 16/20 both keys (fails
   02/03/05/08): Q24 blocks G3. G5 scored (results/freeze10_s193/G5_SCORES.md): all rows pass both keys except
   G5.5 o2_circle_z s1 0.5027 m (limit 0.5); PID ref 1.14-1.16 m (g55_pid_ref/): Q25 blocks the G5 verdict.
   G5.9a key2 reference-definition difference as freeze-8/9 (key 1 PASS). G2 PASSED at freeze-10 (S194).
   Next: act on Q24/Q25 answers when present; otherwise G7 items (item 5) one task per session.
   Binary built 22:38 after 7fe6206fcc, no src commit since (checked). G7 harness starts after the queue ends
   (RC194 item 6 asked parallel; not done: a docker build during gate flights risks the binary and timing).
1-2. G2 and G4 PASSED at freeze-10 (S194, GATES.md verdicts). A FREEZE-11 (Q24 A) would invalidate them again.
3. G5 history: freeze-9 (G5_SCORES.md) every flown row PASS both keys; G5.5 worst H 0.499 m (o2 s3, limit 0.5: thin, no
   chase). G5.10 (SAT dropped Q21) stabilized part PASS 3/3 both keys (freeze9_s183/g510_stab, S188).
   D-FREEZE-9-GAP re-fly (S188, freeze9_s183/g5_modes): G5.1 6/6 and G5.2 6/6 PASS both keys; G5.7 FAIL 3/3 both
   keys on hold-edge tracking lag (freeze-9). FREEZE-10 probe: G5.7 PASS 3/3 (worst 3.61 deg); score in item 0.
4. G3: D-AF-ALIAS fixes 2d92dbcf59 + 4afa7a97b6 (keyed) re-flown S191 (results/g3_pretest_s190/README.md): key1
   15/20, key2 16/20, 2.5-7.3 Hz lines gone. Left: q 2.0 Hz on 02/05/19 (INDI-only in S188 PID refs; 02/05 also
   item 3 ~0.5 m), 03 (2.0 Hz) and 08 (10.75 Hz) shared with PID. Cause search S191 (CAUSE_S191.md): 02/05 =
   1.45 Hz accel-loop oscillation (q 12.2/8.5 dps vs PID 0.4/0.5; "2.0 Hz" = detector band floor), setpoints
   steady; 02/05 = the two most uncompensated GNSS draws (+95/+84 ms, passing max +59): consistent, not shown ->
   S192 matched-GNSS probe: 02/05 pass items 1-3 both keys -> cause shown = uncompensated GNSS +95/+84 ms (PID
   passes them): if they fail at freeze-10, re-open D-OFFB-POSVEL or ask owner on mismatch range (D-FREEZE-10).
   19 = key 1 scores the land pulse (key 2 stops at land): scope, not osc. 03 PID q 2.5 Hz key 1 only; 08 PID p
   11 Hz vs INDI q 10.75 Hz. GATES l.555 Q15 A nav-change skip is filed under G4 item 2, not G3. Shared 03/08 ->
   owner question with G3 verdict data.
5. G7 (stage 7, not before G2/G4/G5 verdicts): module harness (D-G7-HARNESS) incl. MC_INDI_ID_OK call site
   (K128 MAJOR), D-JFF-SOURCE case, D-OFFB-POSVEL wiring test, omega_ff step on offboard entry (key2_jffoffb MINOR),
   checker self-tests passthrough/offb_vel DONE S194 (defects listed in bench/tests/SELFTEST_G7_S194.md: no verdict,
   no LOC check in offb_vel_check, IndexError on empty topic; confirm which script scored G5.5 offb_vel_step), g511 yaw p95 subtraction test (g511_check.py:184), g510
   MPC_TILTMAX_AIR log-read branch (g510_check.py:115-119); ACT_TC/W_MAX firmware vs bench (lesson 12); guard
   params (ERPM_TO/FRZ, SP_TO, DT_MAX) unevidenced.
Deferred to before G6: yaw fit fix (r regressor + matched grid = probe V3, K126 MAJORs, A-44).
Rules: 1 session per inner-loop law change; parallel docker streams only for tolerance-insensitive probes, never gate
  evidence; G3 evidence for INDI outer loop needs MC_INDI_POS_EN=1. Next RC: S209 (RC194 done).
STOP list (+RC194: A-53/A-54/A-58 bound-only, A-50/A-51 model x-check, G5.5 margin): A-39 / yaw measured-path chase, PID M1 hook, hooks without a consumer, stand-alone anomaly chases,
  --sched-anchor and set_param fixes, EdgeState design, more PID G5.10 runs.
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
- quad5in defaults: bench/params/quad5in_indi_defaults.params (ACT_TC 0.033); firmware ACT_TC 0.05, MC_INDI_ID_OK 0
  halves K.
- Guard blocks long `git commit -m`: use `-F <file>`.
- chatter_cruise_s176.py without RAW= overwrites tracked results/g4_gate_s169/chatter_cruise_s176_raw.txt: brief
  agents to set RAW to their own folder; `git checkout` it if dirty.
- Detached chains: list every waiter pid in Tasks in flight; an unlisted S187 chain flew g3_pid_ref_s187 in S188.- Logger misses the first ~0.2 s of indi_pos_status (late subscription): never read a missing sample as bypass.
## Tasks in flight
| id | task | agent | output | resume |
|---|---|---|---|---|
| Q10 | FREEZE-10 re-fly queue: ENDED 01:14 S194, all 4 steps rc 0 | - | results/freeze10_s193/ | - |
| S195a | G7(d) check_format + G7(e) NuttX flash/RAM (no source change) | sonnet | results/g7_s195/FORMAT_SIZE.md | relaunch brief |
| S195b | G7(c) firmware defaults vs validated params table | sonnet | results/g7_s195/DEFAULTS_DIFF.md | relaunch brief |
(none; S194 checker self-tests committed: bench/tests/test_passthrough_check.py, test_offb_vel_check.py)
(S189 agents done and committed. Build probes: guard denies a segment naming indi_project with
rm/tee/git apply etc.; run each run.sh call alone, redirect only into indi_flight/.)

## Open problems
- Deferred to stage 7 (RC98): MINORs frozen-b on saturated motor, lagging mean_u at reset, lower mean_u limit
  untested, DESCEND failsafe tests.
- Review notes (`indi_project/review/external_review_s59_notes/`): `module_parity.md` for stage 5.
- Unmodelled in margins_models.py: measured path = eta x motor state, yaw structure (A-51), attitude loop; 267 Hz
  analytic only. Motor latency now optional (lat_s, S175).
- Deferred anomalies: A-4, A-6, A-30, A-32, A-34-A-36, A-39.
