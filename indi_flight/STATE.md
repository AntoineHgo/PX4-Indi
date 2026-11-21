# STATE (budget 8000 bytes: read at every launch, resume essentials only)

## Status
- Stage: 6 (validation). FREEZE-7 declared S177 (D-FREEZE-7): firmware 08011e92d0, config g5_freeze_s157 params.
  Rows listed in D-FREEZE-7 re-fly now (queue results/freeze7_s177); other freeze-6 evidence stands.
- Gates: see GATE_STATUS.tsv. Owner answers Q8-Q15 acted on S175 (GATES "Owner amendments S175", D-OWNER-Q8-Q15).
- Blocker: none for G2/G4/G5.3-5.5. G5.10 stabilized-part scoring waits Q17 (BLOCKING for G5.10). G4 NOT PASSED
  at freeze-7 (chatter); cause search done S178, no fix shown: step back (action 2).
## Next actions (owner order; each names its gate item)
1. G2: when g2_outer_freeze7_s177 (24) and g2_spot_freeze7_s178 (2) are scored and all pass: write verdict PASSED
   (GATES G2 + GATE_STATUS) with the 3 rate x-check groups as evidence limit (A-51 open). A fail re-opens G2
   (D-FREEZE-7 overturn rule). No model-structure work.
2. G4 NOT PASSED freeze-7. Step back DONE S179: D-G4-STEPBACK re-opens (3) outer measured-force filter
   MC_INDI_POS_LPF for L2 (20-22 Hz descent, predates the 2x gains: freeze-6 flagged it too) and (2) offboard
   setpoint zero-order hold for L1 (33 Hz). Fix probes: F1 (LPF 5, cruise_typ s1-s3, in flight, task F1) then F2
   (firmware: offboard setpoint extrapolation, cruise_typ s1; implement only after queues 2-4 end, no rebuild while
   gate queues fly; firmware key2 + unit test before freeze-8). Act per the D-G4-STEPBACK overturn rule. A probe
   that removes both lines -> freeze-8 (config/firmware), re-fly G4 18, G5.5 24, G2 outer 24, G5.3 (hold+mission)
   and G5.4 if LPF moves. Do NOT propose the 3 s skip for chatter.
3. G5: freeze-7 G5.5 24/24, G5.3 mission 3/3, G5.4 6/6 PASS (SCORES.md). G5.3 hold (gust_x) IS in the D-FREEZE-7 list
   ("G5.3/G5.4 x3") and unflown: fly 3 seeds at the final freeze (deferred while F1/F2 may move the config). G5.10 pre-test queue4 (results/g5_10_freeze7_s178, after queue3): read
   SAT motors >= 0.99 time (score_motors.py is NEW: key2 before gate use) and PID reference; stabilized part waits
   Q17. Then G5.10 3 seeds, then G5 verdict.
4. G3 set-up (owner step 4), after G2/G4/G5 queue: tel_frozen hook (gz_bridge bit-identical rpm injector, two keys;
   until then runs 03/11 abort); (b) excursion vs setpoint in g3_checks (key2 before gate use); run 17 LOC (tilt
   129 deg): PID reference only, one session max; osc runs 03/07/08/13 are re-flown after the set-up fix, not chased.
   Then re-fly the 20-run pre-test; when clean, write "G3 set-up fixed, ready for flight chain" here + WAIT_OWNER.
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
- Logger misses the first ~0.2 s of indi_pos_status (late subscription): never read a missing sample as bypass.
## Tasks in flight
| id | task | agent | output | resume |
|---|---|---|---|---|
| Q7 | freeze-7 serial queue G5.5 24 + G4 18 + G5.3/5.4 (detached) | sonnet | results/freeze7_s177/ (queue_status.tsv) | re-run queue.sh (idempotent), see its README |
| G2Q | G2 outer 24 cells re-fly (flying since 13:30; dir dirty while flying) (model predicts xy PM 46 deg, GM 7.8 dB) | sonnet | results/g2_outer_freeze7_s177/ | queue2.sh (idempotent), README scoring cmd |
| Q4 | G5.10 pre-test 4 flights, queue4 detached after queue3 (4 h wait cap from 13:32) | - | results/g5_10_freeze7_s178/ (queue4.log) | rerun queue4.sh |
| SP2 | G2 spot cells roll800_fwdef_s2 + att pitch400_s1, queue3 detached, waits on queue2 (max 3 h from 13:30: on WAIT_TIMEOUT in queue3.log rerun) | sonnet | results/g2_spot_freeze7_s178/ | README resume cmd |
| SG2 | S179: score G2 outer 24 cells after queue2 ends, then the 2 spot cells | sonnet | results/g2_outer_freeze7_s177/SCORES.md, results/g2_spot_freeze7_s178/SCORES.md | re-brief from its README scoring cmd |
| F1 | S179 G4 fix probe F1 (D-G4-STEPBACK): MC_INDI_POS_LPF 5, cruise_typ s1-s3 | sonnet | results/g4_fix_probe_s179/README.md | re-brief from README |

## Open problems
- Deferred to stage 7 (RC98): MINORs frozen-b on saturated motor, lagging mean_u at reset, lower mean_u limit
  untested, DESCEND failsafe tests.
- Review notes (`indi_project/review/external_review_s59_notes/`): `module_parity.md` for stage 5.
- Unmodelled in margins_models.py: measured path = eta x motor state, yaw structure (A-51), attitude loop; 267 Hz
  analytic only. Motor latency now optional (lat_s, S175).
- Deferred anomalies: A-4, A-6, A-30, A-32, A-34-A-36, A-39.
