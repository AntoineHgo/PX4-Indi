# STATE (budget 8000 bytes: read at every launch, resume essentials only)

## Status
- Stage: 6 (validation). FREEZE-7 declared S177 (D-FREEZE-7): firmware 08011e92d0, config g5_freeze_s157 params.
  Rows listed in D-FREEZE-7 re-fly now (queue results/freeze7_s177); other freeze-6 evidence stands.
- Gates: see GATE_STATUS.tsv. Owner answers Q8-Q15 acted on S175 (GATES "Owner amendments S175", D-OWNER-Q8-Q15).
- Blocker: none (Q17, Q18 answered A, logged S180).
  G2 and G4 NOT PASSED at freeze-7; freeze-8 in preparation (XY_P 1.2 shown, F2 for L1 to implement).
## Next actions (owner order; each names its gate item)
1. Freeze-8 (G2, G4 cruise, G5): candidate firmware = F2 9dd5f76382 + F4 d65111154b (kSetpointLeadTc 0.03) +
   MC_INDI_XY_P default 1.2 (d2f3845292; bench model test 1d9ae87085). F4 met its probe on cruise_typ_s1 (89 Hz
   4.2e-4, limit 5e-4, thin). Before freeze: (a) F4 gtest DONE; (b) key2 (sonnet, code-to-spec) of F2+F4+XY_P diff
   IN FLIGHT S181 -> design/key2_freeze8_s181.md; (c) pre-test IN FLIGHT S181 -> results/freeze8_pretest_s181/: cruise_typ s2/s3 + G2-STEP
   attitude cell. Then declare freeze-8 (D-FREEZE-8, list rows) and re-fly: G2 outer 24 + 2 spot + G2-STEP, G4 18,
   G5.5 24, G5.3 hold+mission x3, G5.4 6, G5.10 3 seeds (Q17 A scoring).
2. G4 hover_harsh_s1 20 Hz (take-off/loiter, 9.7e-4, PID clean, 1/3 seeds): after F2 result; one session cause bound,
   candidate decision (4) inner rate INDI -> owner question before re-opening (re-flies most gates).
   Q18 re-score done (no verdict moved); cruise item 3 offset is not a G4 row (PID 0.295 m = INDI): closed.
3. G5: freeze-7 G5.5 24/24, G5.3 mission 3/3, G5.4 6/6 PASS (SCORES.md). G5.3 hold (gust_x) IS in the D-FREEZE-7 list
   ("G5.3/G5.4 x3") and unflown: fly 3 seeds at the final freeze (deferred while F1/F2 may move the config). G5.10 pre-test queue4 (results/g5_10_freeze7_s178, after queue3): read
   SAT motors >= 0.99 time (score_motors.py is NEW: key2 before gate use) and PID reference; stabilized part per Q17 A
   (GATES "Owner amendments S180"). Then G5.10 3 seeds, then G5 verdict.
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
| - | G5.10 pre-test queue4 flown, 4 metrics committed, unscored | - | results/g5_10_freeze7_s178/ | - |
| K8 | key2 freeze-8 diff (S181) | sonnet | design/key2_freeze8_s181.md | re-brief if file has no verdict line |
| P8 | freeze-8 pre-test 3 flights (S181) | sonnet | results/freeze8_pretest_s181/README.md | re-run missing items |

## Open problems
- Deferred to stage 7 (RC98): MINORs frozen-b on saturated motor, lagging mean_u at reset, lower mean_u limit
  untested, DESCEND failsafe tests.
- Review notes (`indi_project/review/external_review_s59_notes/`): `module_parity.md` for stage 5.
- Unmodelled in margins_models.py: measured path = eta x motor state, yaw structure (A-51), attitude loop; 267 Hz
  analytic only. Motor latency now optional (lat_s, S175).
- Deferred anomalies: A-4, A-6, A-30, A-32, A-34-A-36, A-39.
