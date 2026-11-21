# STATE (budget 8000 bytes: read at every launch, resume essentials only)

## Status
- Stage: 6 (validation) on freeze-6 firmware 23acbdef67 + post-freeze commits kept (D-JFF-KEEP). Q11 B forces a
  freeze-7 (offboard pos/vel feedback in the INDI module); rows invalidated by D-JFF-KEEP and Q11 B re-fly there.
- Gates: see GATE_STATUS.tsv. Owner answers Q8-Q15 acted on S175 (GATES "Owner amendments S175", D-OWNER-Q8-Q15).
- Blocker: G2 verdict waits Q16 (BLOCKING for G2). G4 chatter: INDI-specific AUTO_LAND line, probe S175-f.
## Next actions (owner order; each names its gate item)
1. G2: no work until Q16 answered. On A: write verdict PASSED (GATES G2 + GATE_STATUS) with A-51 as evidence limit.
2. G4: item 2 PASS both keys (Q15 A). Chatter clause FAIL: ~22 Hz command line AUTO_LAND entry -> touchdown (~10 s,
   3-8 DShot steps), INDI only, PID ref none (results/g4_gate_s169/chatter_s175.md). INDI-specific gate failure: no
   owner question; the 3 s skip would only break the streak, do NOT propose it. Probe S175-f: is it gone with
   aa4fd2654a (FF offboard-only)? If yes: D-JFF-KEEP is a shown fix, G4 re-fly at freeze-7. If no: one session of
   cause search (land descent in mc_indi_pos_control), then re-open the decision. Key1 width bug (+-0.5 Hz) in S175-f.
   G4 rows were flown at freeze-6: re-fly at freeze-7 (D-JFF-KEEP).
3. G5 re-score (owner step 2): G5.2 z band max(2 % d, 0.10 m) (Q10 B); G5.9a ref actuator_armed.kill (Q8 add.2);
   G5.11 xy truth excursion + yaw p95 jump (Q12 B+D); G5.10 tilt <= TILTMAX+5 (Q9 a); G5.6 false maybe_landed and
   G5.11 z "not tested Q8(b)". Checker changes get key2 before counting. Evidence: results/g5_freeze_s157, g511_fix_s161.
4. G5.5 (owner step 3, Q11 B): design note (1 page) + DECISIONS entry for INDI-module pos/vel feedback with flatness
   FF in offboard only; fable review of the design; then code + key2 + tests; G5.5 pre-test; check whether G2 outer
   cells / G4 cruise were flown in offboard (then re-fly them at freeze-7).
5. G5.10 re-definition flights (Q9 b/c): SAT part one-flight check motors >= 0.99, full-scale stabilized part.
6. G3 set-up (owner step 4): S175-e does (a) abort on not_applied + noise-profile cause, (c) Docker scoring.
   Still to do: (b) excursion vs setpoint in g3_checks (key2 before gate use); tel_frozen hook (sim hook, two keys);
   (d) run 17 LOC (tilt 129 deg) and osc runs 03/07/08/13/17: PID reference first, one session max. Then re-fly the
   20-run pre-test; when clean, write "G3 set-up fixed, ready for flight chain" here and create WAIT_OWNER.
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
| S175-f | G4 chatter probe post-JFF + key1 width fix | sonnet | results/g4_chatter_probe_s175/README.md | re-brief from file |
| S175-e | G3 set-up (a) abort on not_applied, noise cause, (c) Docker score | sonnet | results/g3_setup_s175/README.md | re-brief from file |

## Open problems
- Deferred to stage 7 (RC98): MINORs frozen-b on saturated motor, lagging mean_u at reset, lower mean_u limit
  untested, DESCEND failsafe tests.
- Review notes (`indi_project/review/external_review_s59_notes/`): `module_parity.md` for stage 5.
- Unmodelled in margins_models.py: measured path = eta x motor state, yaw structure (A-51), attitude loop; 267 Hz
  analytic only. Motor latency now optional (lat_s, S175).
- Deferred anomalies: A-4, A-6, A-30, A-32, A-34-A-36, A-39.
