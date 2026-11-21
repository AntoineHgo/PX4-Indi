# STATE (budget 8000 bytes: read at every launch, resume essentials only)

## Status
- Stage: 6 (validation). FREEZE-9 declared S183 (D-FREEZE-9): firmware 83976c5099 (MC_INDI_XY_VP default 2.4,
  D-XY-PICK), config g5_freeze_s157 params (XY gains at firmware defaults 1.2/2.4). D-FREEZE-8 list re-flies in
  queue results/freeze9_s183 (G4 cruise_harsh_s2 excluded until Q19).
- Gates: see GATE_STATUS.tsv. Owner answers Q8-Q15 acted on S175 (GATES "Owner amendments S175", D-OWNER-Q8-Q15).
- Blocker: Q20 (G4), Q21 (G5.10), Q22 (G3) open; G7 waits G4/G5 verdicts -> WAIT_OWNER (S186).
## Next actions (owner order; each names its gate item)
1. G2 PASSED at freeze-9 (S184, GATES "G2 verdict at freeze-9"). Any firmware change re-opens it.
2. G4 NOT PASSED at freeze-9 (S184): only the PID guard fails (INDI 20 Hz line 5.0-5.3e-4 in skipped windows at
   17->4 and 14->18). Q20 (guard metric, options A strict / C) BLOCKING for G4: no G4 work until answered.
   Cause search done S184 (g4_20hz_cause_s184): 17->4 transient in both stacks, INDI 1.7x; 14->18 guard artefact.
   Freeze-8 G4 Q19 re-score (history) waits Q20. Guard comparison is not coded (Q19_KEY2_REVIEW F1): after Q20,
   one script + second key.
3. G5: freeze-9 (G5_SCORES.md) every flown row PASS both keys; G5.5 worst H 0.499 m (o2 s3, limit 0.5: thin, no
   chase). G5 verdict waits G5.10 only. Q21 (SAT set-up, options A demand transient / B hover param / C drop SAT)
   BLOCKING for G5.10: no G5.10 flight or score until answered. After the answer: scenario per answer (S184 patches
   in results/g510_setup_s184), one-flight check, 3 seeds INDI + PID ref (fly.sh), stabilized part Q17 A, scorer
   bench/g510_score_motors.py (keyed S181), then G5 verdict.
4. G3: Q22 (attitude-loop boundary e x tau_mult >= ~5 vs the G3 box; options A P~4.7 + freeze-10 / B narrow /
   C scheduled P / D report) BLOCKING for G3: no G3 flight or score of osc rows until answered. Set-up done S186:
   tel_frozen hook (anchored to traj/stick segment, checked), excursion vs setpoint (2 keys agree), chatter out of
   item 2, run_validity pid_*, key2 item 3 on window + setpoint (agree 20/21). Open tooling before G3 scoring:
   constant 5 mm altitude-mean offset key1 vs key2 (run 07 -0.102 vs -0.097 at the 0.10 limit;
   results/g3_excursion_s186/KEY2_ITEM3_S186.md): trace which origin is right (one sonnet task).
   After Q22: act on answer, re-fly the 20-run pre-test; when clean, write "G3 set-up fixed, ready for flight chain"
   here + WAIT_OWNER.
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

## Open problems
- Deferred to stage 7 (RC98): MINORs frozen-b on saturated motor, lagging mean_u at reset, lower mean_u limit
  untested, DESCEND failsafe tests.
- Review notes (`indi_project/review/external_review_s59_notes/`): `module_parity.md` for stage 5.
- Unmodelled in margins_models.py: measured path = eta x motor state, yaw structure (A-51), attitude loop; 267 Hz
  analytic only. Motor latency now optional (lat_s, S175).
- Deferred anomalies: A-4, A-6, A-30, A-32, A-34-A-36, A-39.
