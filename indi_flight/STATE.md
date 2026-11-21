# STATE (budget 8000 bytes: read at every launch, resume essentials only)

## Status
- Stage: 6 (validation). FREEZE-9 declared S183 (D-FREEZE-9): firmware 83976c5099 (MC_INDI_XY_VP default 2.4,
  D-XY-PICK), config g5_freeze_s157 params (XY gains at firmware defaults 1.2/2.4). D-FREEZE-8 list re-flies in
  queue results/freeze9_s183 (G4 cruise_harsh_s2 excluded until Q19).
- Gates: see GATE_STATUS.tsv. Owner answers Q8-Q15 acted on S175 (GATES "Owner amendments S175", D-OWNER-Q8-Q15).
- Blocker: none (Q19 answered A + PID guard, logged S183: GATES "Owner amendment S183", D-OWNER-Q19).
## Next actions (owner order; each names its gate item)
1. G2 at freeze-9 (results/freeze9_s183/G2_SCORES.md): margins 26/26 + G2-STEP 9/9 (yaw 1180 ms); spot rate
   PM 47.3 (re-fly, holes PASS) / att 47.4. Hole re-flies (README "Hole re-fly"): 3 outer cells failed holes twice
   (2nd attempt under host load); 3rd attempt in agent S183-G (holefail_first/, holefail_second/ kept). When clean
   (or holes <= 0.1 % per GATES evidence limit 1 with margins unchanged): write G2 verdict in GATES + GATE_STATUS.
2. G4 at freeze-9: agent S183-G flies cruise_harsh_s2 + PID refs (g4_pid/), key2 copy with Q19 skip (*_q19.py:
   new metric change, give it a second key before the verdict), PID guard table, G4_SCORES.md -> G4 verdict.
   Then re-score freeze-8 G4 with keyed scripts (owner Q19 order, history, no re-fly).
3. G5: freeze-9 (G5_SCORES.md) every flown row PASS both keys; G5.5 worst H 0.499 m (o2 s3, limit 0.5: thin, no
   chase, the D-XY-PICK trade). G5 verdict waits G5.10 only. G5.10: (a) scorer
   bench/g510_score_motors.py keyed S181; SAT_MIN_FRAC is validity only (verdict INVALID); (b) SAT set-up fault (D-G510-SAT-SETUP):
   ramp SIM_GZ_THR_SC in hover before the window, pre-test INDI + PID 1 seed; (c) then 3 seeds INDI (+PID ref),
   stabilized part Q17 A; then G5 verdict. Run after the freeze-8 queue (no parallel docker for gate evidence).
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
- chatter_cruise_s176.py without RAW= overwrites tracked results/g4_gate_s169/chatter_cruise_s176_raw.txt: brief
  agents to set RAW to their own folder; `git checkout` it if dirty.
- Logger misses the first ~0.2 s of indi_pos_status (late subscription): never read a missing sample as bypass.
## Tasks in flight
| id | task | agent | output | resume |
|---|---|---|---|---|
| S183-G | G2 3-cell hole re-fly + G4 cruise_harsh_s2, PID refs, Q19 key2, G4_SCORES | sonnet | results/freeze9_s183/README.md, G4_SCORES.md | rerun results/freeze9_s183/queue.sh (skips done), then G4 part from README |

## Open problems
- Deferred to stage 7 (RC98): MINORs frozen-b on saturated motor, lagging mean_u at reset, lower mean_u limit
  untested, DESCEND failsafe tests.
- Review notes (`indi_project/review/external_review_s59_notes/`): `module_parity.md` for stage 5.
- Unmodelled in margins_models.py: measured path = eta x motor state, yaw structure (A-51), attitude loop; 267 Hz
  analytic only. Motor latency now optional (lat_s, S175).
- Deferred anomalies: A-4, A-6, A-30, A-32, A-34-A-36, A-39.
