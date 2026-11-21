# STATE (budget 8000 bytes: read at every launch, resume essentials only)

## Status
- Stage: 6 (validation). FREEZE-8 declared S181 (D-FREEZE-8): firmware d2f3845292, config g5_freeze_s157 params
  (XY gains at firmware defaults 1.2/3.6). Rows listed in D-FREEZE-8 re-fly (queue results/freeze8_s181).
- Gates: see GATE_STATUS.tsv. Owner answers Q8-Q15 acted on S175 (GATES "Owner amendments S175", D-OWNER-Q8-Q15).
- Blocker: none (Q17, Q18 answered A, logged S180).
  G2 and G4 NOT PASSED at freeze-7; freeze-8 re-fly decides them.
## Next actions (owner order; each names its gate item)
1. FREEZE-8 queue results/freeze8_s181/queue.sh (resume: rerun it; `tail -n 5 queue_status.tsv`, docker ps). G2
   scored S182: NOT PASSED (GATES "G2 verdict at freeze-8": outer 24/24 PASS, spot rate PM 41.3 / att 42.2 FAIL).
   Score G4 (gate_g4.sh score + keys used at freeze-7) and G5 groups as they finish, verdicts same session.
   Yaw G2-STEP settle 1139 ms (S64 ~920, limit 1350): watch in the 3 seeds, no chase while in limit.
1b. G2 spot cause (one session, started S182; design/g2_spot_cause_s182.md): low-f phase loss (<3 Hz) both cells
   tracks MC_INDI_XY_VP 1.8 -> 3.6 (freeze-7, kept at freeze-8); att 4-8 Hz lag at freeze-8 looks like F4
   (kSetpointLeadTc 0.03, constexpr). No PID injection path exists (stock code, out of scope): PID-ref-first not
   applicable. P1/P2 flown S182 (results/g2_spot_probe_s182): XY 0.95/1.8 -> PM 49.0 / 51.4: cause shown (D-XY-TRADE).
   NEXT: sweep XY_VP {2.4, 2.8} (XY_P 1.2): per pair spot rate + att cell + G5.5 o1/o3/o7 s1 (one sonnet agent, copy
   results/g2_spot_probe_s182/fly.sh + queue.sh fly()); pick the pair passing PM >= 45 and G5.5 <= 0.5 m; set it as
   firmware default (two keys), freeze-9, re-fly the D-FREEZE-8 list. No pair -> F4-revert probe, then owner question.
2. G4 freeze-8 scored S182 (G4_SCORES.md): all rows in limits except cruise_harsh_s2 20 Hz at hold->land switch,
   keys split on the Q15 skip -> Q19 BLOCKING for G4 (no G4 work until answered; A = PASSED). If a freeze-9 follows
   from the G2 spot fix, G4 re-flies anyway.
3. G5: freeze-8 (results/freeze8_s181/G5_SCORES.md) all scored rows PASS incl. G5.3 hold 3/3; G2-STEP 9/9 (yaw settle
   1208 ms s1, limit 1350, rising since S64 ~920: no chase while in limit). G5.10: (a) key2 done (KEY2_MOTORS_S181.md): sat times agree, key1
   score_motors.py has 4 defects (exit_status LOC, stab tilt limit MAN_TILT_MAX, recovery = att error to stick sp,
   KeyError on aborted runs): FIXED S181 -> bench/g510_score_motors.py, keys AGREE; SAT_MIN_FRAC is now validity
   only (verdict INVALID, S182 825bec01b8); (b) SAT set-up fault (D-G510-SAT-SETUP):
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
| - | none | - | - | - |

## Open problems
- Deferred to stage 7 (RC98): MINORs frozen-b on saturated motor, lagging mean_u at reset, lower mean_u limit
  untested, DESCEND failsafe tests.
- Review notes (`indi_project/review/external_review_s59_notes/`): `module_parity.md` for stage 5.
- Unmodelled in margins_models.py: measured path = eta x motor state, yaw structure (A-51), attitude loop; 267 Hz
  analytic only. Motor latency now optional (lat_s, S175).
- Deferred anomalies: A-4, A-6, A-30, A-32, A-34-A-36, A-39.
