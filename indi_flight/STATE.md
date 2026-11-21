# STATE (budget 8000 bytes: read at every launch, resume essentials only)

## Status
- Stage: 6 (validation). FREEZE-9 declared S183 (D-FREEZE-9): firmware 83976c5099 (MC_INDI_XY_VP default 2.4,
  D-XY-PICK), config g5_freeze_s157 params (XY gains at firmware defaults 1.2/2.4). D-FREEZE-8 list re-flies in
  queue results/freeze9_s183 (G4 cruise_harsh_s2 excluded until Q19).
- Gates: see GATE_STATUS.tsv. Owner answers Q8-Q15 acted on S175 (GATES "Owner amendments S175", D-OWNER-Q8-Q15).
- Blocker: G5.7 waits for Q23 (fix choice for D-G57-FF). Causes shown on logs S189: G3 7 Hz = D-AF-ALIAS
  (outer a_f aliased by 88.9 Hz stage decimation), G5.7 = D-G57-FF (rate FF off outside offboard, aa4fd2654a).
## Next actions (owner order; each names its gate item)
1. G2 PASSED at freeze-9 (S184, GATES "G2 verdict at freeze-9"). Any firmware change re-opens it.
2. G4 PASSED at freeze-9 under Q20 (S187, both guard keys 0 checked / 0 FAIL). Any firmware change re-opens it.
3. G5: freeze-9 (G5_SCORES.md) every flown row PASS both keys; G5.5 worst H 0.499 m (o2 s3, limit 0.5: thin, no
   chase). G5.10 (SAT dropped Q21) stabilized part PASS 3/3 both keys (freeze9_s183/g510_stab, S188).
   D-FREEZE-9-GAP re-fly (S188, freeze9_s183/g5_modes): G5.1 6/6 and G5.2 6/6 PASS both keys; G5.7 FAIL 3/3 both
   keys on hold-edge tracking lag. Cause shown S189 (D-G57-FF): aa4fd2654a revert probe PASS s3/s1. Fix waits
   for Q23 (BLOCKING G5.7; do not re-fly/score G5.7 meanwhile).
4. G3: D-AF-ALIAS fixes 2d92dbcf59 + 4afa7a97b6 (keyed) re-flown S191 (results/g3_pretest_s190/README.md): key1
   15/20, key2 16/20, 2.5-7.3 Hz lines gone. Left: q 2.0 Hz on 02/05/19 (INDI-only in S188 PID refs; 02/05 also
   item 3 ~0.5 m), 03 (2.0 Hz) and 08 (10.75 Hz) shared with PID. Cause search (one session, S191 agent):
   results/g3_pretest_s190/CAUSE_S191.md. Then FREEZE-10 with the Q23 fix; invalidated: G2 outer, G4, G5 outer
   rows, G3 pre-test. GATES l.555 Q15 A nav-change skip is filed under G4 item 2, not G3. Shared 03/08 -> owner
   question with G3 verdict data.
5. G7 (stage 7, not before G2/G4/G5 verdicts): module harness (D-G7-HARNESS) incl. MC_INDI_ID_OK call site
   (K128 MAJOR), D-JFF-SOURCE case, D-OFFB-POSVEL wiring test, omega_ff step on offboard entry (key2_jffoffb MINOR),
   checker self-tests passthrough_check/offb_vel_check, g511 yaw p95 subtraction test (g511_check.py:184), g510
   MPC_TILTMAX_AIR log-read branch (g510_check.py:115-119); ACT_TC/W_MAX firmware vs bench (lesson 12); guard
   params (ERPM_TO/FRZ, SP_TO, DT_MAX) unevidenced.
Deferred to before G6: yaw fit fix (r regressor + matched grid = probe V3, K126 MAJORs, A-44).
Rules: 1 session per inner-loop law change; parallel docker streams only for tolerance-insensitive probes, never gate
  evidence; G3 evidence for INDI outer loop needs MC_INDI_POS_EN=1. Next RC: S193 (RC178 done, cuts applied).
STOP list: A-39 / yaw measured-path chase, PID M1 hook, hooks without a consumer, stand-alone anomaly chases,
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
| S191-cause | G3 2.0 Hz q cause on 02/05/19, PID signature on 03/08 | sonnet | results/g3_pretest_s190/CAUSE_S191.md | re-brief from STATE item 4 |
(S189 agents done and committed. Build probes: guard denies a segment naming indi_project with
rm/tee/git apply etc.; run each run.sh call alone, redirect only into indi_flight/.)

## Open problems
- Deferred to stage 7 (RC98): MINORs frozen-b on saturated motor, lagging mean_u at reset, lower mean_u limit
  untested, DESCEND failsafe tests.
- Review notes (`indi_project/review/external_review_s59_notes/`): `module_parity.md` for stage 5.
- Unmodelled in margins_models.py: measured path = eta x motor state, yaw structure (A-51), attitude loop; 267 Hz
  analytic only. Motor latency now optional (lat_s, S175).
- Deferred anomalies: A-4, A-6, A-30, A-32, A-34-A-36, A-39.
