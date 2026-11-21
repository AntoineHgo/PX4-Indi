# STATE (budget 8000 bytes: read at every launch, resume essentials only)

## Status
- Stage: 6 (validation) on freeze-6 firmware 23acbdef67 + post-freeze commits kept (D-JFF-KEEP). Q11 B forces a
  freeze-7 (offboard pos/vel feedback in the INDI module); rows invalidated by D-JFF-KEEP and Q11 B re-fly there.
- Gates: see GATE_STATUS.tsv. Owner answers Q8-Q15 acted on S175 (GATES "Owner amendments S175", D-OWNER-Q8-Q15).
- Blocker: G2 verdict waits Q16 (BLOCKING for G2). G4 chatter: cruise 9/9 flagged, cause open (action 2).
## Next actions (owner order; each names its gate item)
1. G2: no work until Q16 answered. On A: write verdict PASSED (GATES G2 + GATE_STATUS) with A-51 as evidence limit.
2. G4: item 2 PASS both keys (Q15 A). Chatter (+-2 Hz width fixed in key1, b2bfa1d48f): s169 (freeze-6) hover 6/9,
   cruise 9/9 flagged, both keys. Hover: INDI-only 22 Hz AUTO_LAND line (chatter_s175.md, PID none) gone in 1 HEAD
   flight (results/g4_chatter_probe_s175; touchdown burst only, not sustained); no same-commit A/B. Cruise (S176,
   chatter_cruise_s176.md): INDI-specific (PID same seed clean): ~89 Hz line through the offboard lemniscate, 9/9,
   only 1.4-1.5x the 5e-4 floor; plus the 20-22 Hz AUTO_LAND line (4-8.6x). The offboard path is replaced at freeze-7
   (Q11 B), so the 89 Hz cause search (1 session max) starts on the first freeze-7 cruise flight if the line persists.
   Re-fly hover + cruise 3 seeds x typ/harsh at freeze-7. Do NOT propose the 3 s skip for chatter.
3. G5 re-score DONE S176, key2 agrees (results/g5_rescore_s176). Open MINORs (fix with G7 checker self-tests):
   no test catches removal of the yaw p95 subtraction (g511_check.py:184); G5.10 MPC_TILTMAX_AIR log-read branch
   untested, silent 20 deg fallback (g510_check.py:115-119). Freeze-7 re-fly re-scores with these checkers.
4. G5.5 (Q11 B): D-OFFB-POSVEL decided S176 (own MC_INDI_XY_P/XY_VP 1.9/3.6, all modes; probe o1 0.289 m). Next:
   firmware (params yaml per instructions files, McIndiPosControl.cpp:599-601) + param test + key2; then G5.5
   o1-o4/o7 x3 seeds at freeze-7. All bench scenarios start in offboard hold: G2 outer cells (g2_outer_freeze_s163)
   and all G4 runs re-fly at freeze-7; G2 rate/att cells spot-check 2.
5. G5.10 re-definition flights (Q9 b/c): SAT part one-flight check motors >= 0.99, full-scale stabilized part.
6. G3 set-up (owner step 4): (a)+(c) DONE S175 (bba6345575, results/g3_setup_s175: noise applied, accel HF x9.1,
   gyro HF unchanged = check imu-noise-scale reaches gyro (one log read); abort on not_applied; g3_score_docker.sh).
   Still to do: tel_frozen hook (gz_bridge bit-identical rpm injector, two keys; until then runs 03/11 abort);
   (b) excursion vs setpoint in g3_checks (key2 before gate use); (d) run 17 LOC (tilt 129 deg) and osc runs
   03/07/08/13/17: PID reference first, one session max. Then re-fly the 20-run pre-test; when clean, write
   "G3 set-up fixed, ready for flight chain" here and create WAIT_OWNER.
7. Freeze-7 re-fly: G4 18 runs, G5.3/G5.4/G5.5 + offboard rows, G5 event rows in hover (cheap confirm).
8. G7 (stage 7): module harness (D-G7-HARNESS) incl. MC_INDI_ID_OK call site (K128 MAJOR), D-JFF-SOURCE case,
   omega_ff step on offboard entry (key2_jffoffb MINOR), checker self-tests passthrough_check/offb_vel_check;
   ACT_TC/W_MAX firmware vs bench (lesson 12); guard params (ERPM_TO/FRZ, SP_TO, DT_MAX) unevidenced.
Deferred to before G6: yaw fit fix (r regressor + matched grid = probe V3, K126 MAJORs, A-44).
Rules: 1 session per inner-loop law change; parallel docker streams only for tolerance-insensitive probes, never gate
  evidence; G3 evidence for INDI outer loop needs MC_INDI_POS_EN=1. Next RC: S178.
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
- Logger misses the first ~0.2 s of indi_pos_status (late subscription): never read a missing sample as bypass.
## Tasks in flight
| id | task | agent | output | resume |
|---|---|---|---|---|
| S176g | D-OFFB-POSVEL firmware (uncommitted diff in src/modules/mc_indi_pos_control) + o1 s1 default-params flight | sonnet | results/g55_posvel_fw_s176/README.md | read README; if diff incomplete, re-brief from D-OFFB-POSVEL |

## Open problems
- Deferred to stage 7 (RC98): MINORs frozen-b on saturated motor, lagging mean_u at reset, lower mean_u limit
  untested, DESCEND failsafe tests.
- Review notes (`indi_project/review/external_review_s59_notes/`): `module_parity.md` for stage 5.
- Unmodelled in margins_models.py: measured path = eta x motor state, yaw structure (A-51), attitude loop; 267 Hz
  analytic only. Motor latency now optional (lat_s, S175).
- Deferred anomalies: A-4, A-6, A-30, A-32, A-34-A-36, A-39.
