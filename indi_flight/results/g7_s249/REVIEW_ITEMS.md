# G7 review open items: closure table (S249, read-only reading)

Source: `indi_project/review/external_review_s59.md` (sec. 0-11) and notes `external_review_s59_notes/`. Method: each
actionable finding mapped by grep to DECISIONS.md (D), ANOMALIES.md (A, open), ANOMALIES_CLOSED.md (AC), GATES.md (G),
design/stage3_items_note.md (S3), design/prefreeze_r3_parity.md (PF3 = per-row verdict on module_parity.md),
report/ (R), results/errata.md and g7_s195, g7_s248, g7_s249. Evidence paths are relative to `indi_flight/`.
Limits of this reading: closure is judged from written records, no log or code was re-run; rows marked "(weak)" rest
on a short grep hit. Statuses: CLOSED fixed with evidence; JUSTIFIED not fixed, reason written; SUPERSEDED moot by an
owner decision or redesign; OPEN no written closure found.

| ref | finding | status | where |
|---|---|---|---|
| 0 | Owner decisions: no PID fallback, all modes, generic target, fresh start | SUPERSEDED | D F-1..F-6 (DECISIONS.md:6-24); report/A_history_errata.md:27-44 |
| 2.1a | Trajectory error scored vs 5 Hz zero-order-held setpoint | CLOSED | GATES G1.1 met (:82), G1.2 truth stamped in sim time (:83); report/A_history_errata.md archive-1 |
| 2.1b | O6 "significant 4 %" and session 54/55 "runs ahead" puzzle are artefacts | CLOSED | report/A_history_errata.md archive-2, archive-3 |
| 2.1c | Truth topic stamped at reception, ~0.1 m timing uncertainty | CLOSED | G1.2 (:83); AC A-12 (truth rate cause found S17) |
| 2.1d | Metrics never recomputed by independent code | CLOSED | G1.3 two keys met (:84); G1.4 self-tests break-checked (:85) |
| 2.2a | Hover-effort criterion measures 0.1 % FS noise floor, ratio vs PID | SUPERSEDED | F-5 (no ratio gate); D-EFFORT-BW (DECISIONS.md:165); G4 absolute limits; archive-6 |
| 2.2b | Effort metric differentiates irregular 290-330 Hz log, no anti-alias | CLOSED | D-EFFORT-BW fixed-bandwidth zero-phase filter; AC A-11 |
| 2.2c | PID hover spread 3.5x unexplained, above 30 Hz | CLOSED | AC A-2 (closed S66 with A-7) |
| 2.2d | Outer-loop hover excess below 30 Hz, cause unknown | OPEN | A-6 (ANOMALIES.md:14) "OPEN, no later evidence"; STATE.md:66 deferred; D-FREEZE-6 (:858) says G4 closes or re-bounds it, no record found |
| 2.3a | Report 8.10 mislabels V' rows (W3/W5 swapped) | CLOSED | report/A_history_errata.md archive-4 |
| 2.3b | "1 kHz gyro" claims; rate loop actually 500 Hz, pos 125 Hz | CLOSED | archive-5; D-SIM-STEP (DECISIONS.md:92) |
| 2.3c | Set O arms B and C (feedforward share) never flown | SUPERSEDED | F-5 (no PID comparison); FF contribution studied in D-A18-REOPEN/-SOURCE, D-JFF-SOURCE, D-JFF-OFFB |
| 2.3d | Frozen param file uses removed keys, duplicate keys, cannot load | CLOSED | D-DEFAULTS-FW (:668); g7_s195/DEFAULTS_DIFF.md (0 gain mismatches); G7(c) |
| 2.3e | Firmware defaults not a validated configuration (G1, W_MAX, ACT_BLD, YAW_CUT) | CLOSED | D-DEFAULTS-FW; D-G7-DEFAULTS (:1230); design/defaults_audit_s138.md; residual ID_OK 0 start in D-ID-OK-LIMIT (:1480), report/04_limits.md 4.2 |
| 3.1a | Criteria are ratio conjunction vs PID, cannot say safe to fly | SUPERSEDED | F-5; gates G1-G8 in GATES.md |
| 3.1b | Criterion 1 counts unflyable scenarios (H4, W1, W4) as failures | SUPERSEDED | F-5; O-13 (scenario flown once before entering a set) |
| 3.1c | 10-seed p-value is pseudo-replication; run-to-run non-determinism | CLOSED | D-G1.6 (:71); D-SCHED (:107); G1.6 (:87); G3 randomised plant draws, no p-value gate |
| 3.1d | Verdicts should stand as history only | SUPERSEDED | F-4; report/A_history_errata.md |
| 3.2a | pid_tuned has lightly damped 2.57 Hz mode; outer loops untuned | SUPERSEDED | F-5 PID is reference only; no gate uses it |
| 3.2b | Nominal-path gain probably feedforward, measure it | SUPERSEDED | F-5; see 2.3c |
| 3.3 | Final controllers never flown over full matrix | CLOSED | G2 PASSED, G3 flown 300 runs, G4 PASSED, G5 PASSED (GATE_STATUS.tsv); G3 verdict is NOT PASSED, limits in report/04_limits.md |
| 3.4a | Blend Tb 0.1 s lost altitude, unexplained | JUSTIFIED | A-1 PARKED S66, bound Tb 0.3 s, reopen trigger written (ANOMALIES.md:11) |
| 3.4b | Sporadic vertical excursions in hover | JUSTIFIED | A-3 PARKED, merged into A-14, bound 0.15 m (ANOMALIES.md:12) |
| 3.4c | INDI sensitivity to simulation speed factor | OPEN | A-4 "OPEN S66, blocks G2 tables at speed 4" (ANOMALIES.md:13); no later evidence found |
| 3.4d | Failed v2 tuning candidate c12 unexplained | CLOSED | AC A-5 |
| 3.5a | Noise not calibrated against a real log | JUSTIFIED | F-3 (no target airframe, no real log); D-NOISE-PROF (:880) sourced classes, "no first-hand 5-inch measurement" |
| 3.5b | Rotor reaction torque ~1/10 physical, yaw design transfers badly | CLOSED | D-3 (:54-55, J_r scaled for rotorVelocitySlowdownSim); D-G2Y-DERIVE (:241) |
| 3.5c | GNSS zero latency, SENS_GNSS0_DELAY 0 | CLOSED | design/delay_line_impl_s102.md; G3 GNSS box; D-OWNER-Q24 (:1251) +-50 ms mismatch |
| 3.5d | No battery model in simulator | JUSTIFIED | thrust sag 1.0-0.7 injected in G3/G5.10 (GATES :282, :382); gap remedy D-GAP absorbs sag; PF3 T1.2 DEFERRED; no voltage model, not written as a limit (weak) |
| 3.5e | World-fixed wrench injectors; payload without inertia; CoM torque world-fixed | CLOSED | design/bench_port_plan.md:55 (body-frame com_shift, payload inertia); G1.5 checks JOURNAL.md:805; AC A-31, results/errata.md E-1. Wind drag part: see 11.2c |
| 3.5f | One airframe, one loop rate | SUPERSEDED | F-3 one reference airframe, outlook airframes in G6; D-RATE267, G2 at 267/400/800 Hz |
| 4.1 | No stability analysis, no loop margins | CLOSED | D-G2-BREAK (:191); G2 PASSED, results/freeze10_s193/G2_SCORES.md; report/g2_margins.md |
| 4.2a | Blend is a patch with unknown margin | CLOSED | D-RATE-BLD (:462), D-RATE-BLD-EDGE; D-RATE-BLD-2 chain (:1386-1470) after G3 draw 264; G2 margins at Tb 0.3 |
| 4.2b | Alternative design note: per-motor command-to-omega^2 correction | CLOSED | D-RATE-BLD "Alternatives" (:466, (ii) slow per-motor) |
| 4.3 | Battery voltage: W_MAX constant, HF gain error untested | JUSTIFIED | PF3 T1.2 DEFERRED (steady gap by blend, ESC telemetry); D-GAP; thrust-sag draws in G3 (see 3.5d) |
| 4.4 | Yaw slow, G2 unused, compute spin-up from rotor acceleration | CLOSED | D-G2Y-DERIVE (:241); D-YAW-INV (:299); D-KY (:739); G2 yaw cells |
| 4.5 | maybe_landed zeroes feedback torque in flight | CLOSED | D-S3-LANDED (:353); S3 sec. 1; PF3 T3.1; G5.6 row (:378) was not flown (owner Q8(b), GATE_STATUS G5 note) |
| 4.6a | Filter matching at 400/800 Hz controller rate | CLOSED | G2 rate cells at 267/400/800 Hz (GATES.md:165; A-51 x-check) |
| 4.6b | Notch filters not mirrored on the torque path | OPEN | no hit for "notch" except a margin remark (GATES.md:160); not in report/04_limits.md |
| 4.7 | No in-flight fallback to PID | SUPERSEDED | F-1 (DECISIONS.md:7); review sec. 0 |
| 4.8 | Robustness evidence thin (G1 x0.8/1.3 only, delay never varied) | CLOSED | G3 randomised campaign (GATES :282 box, 300 runs); NOT PASSED, limits report/04_limits.md 4.1; G6 item 7 |
| 5.1 | Thrust-gap standing error on thrust axis, no integral action | CLOSED | D-GAP (:416) blend b; G5.10 sag/saturation (:382); results/g5_g510_s151 |
| 5.2a | `_landed or maybe_landed` zeroes rates and thrust; mode cannot take off | CLOSED | PF3 T3.1, T3.2 (stock takeoff ramp state machine); D-F7-GROUND (:725); G5.4 |
| 5.2b | Failure path only prints; arming reply always true; commander not told | JUSTIFIED | D-PREFREEZE-R2 F1 (:824) same as stock; PF3 T3.4/T3.9 DEFERRED, T3.5 N/A; report/06_bringup_checklist.md |
| 5.2c | Mode serves no pilot mode, hold, RTL, land | SUPERSEDED | F-2, F-6; D-ALTCTL-Z (:550); G5.1-G5.8 |
| 5.2d | EKF reset counters ignored | CLOSED | PF3 T3.8 (EkfResetDetectTest); D-T10-RESET (:890); G5.11 xy/yaw (z part "not tested", Q8(b)) |
| 5.2e | No module-level test of the outer module | CLOSED | D-G7-HARNESS (:564); src/modules/mc_indi_pos_control/*Test.cpp; gaps listed in 11.3e |
| 5.2f | Take-off impossible, no landing handling | CLOSED | PF3 T3.2, T3.3; D-F7-GROUND |
| 5.2g | `setpoint_config` published once, reply not read | CLOSED | PF3 T3.6 N/A (module is the position controller, no external-mode registration) |
| 5.2h | Offboard attitude/rate/actuator setpoints ignored; 100 ms hold | CLOSED | PF3 T3.7 N/A (stock offboard branch kept); D-STAGE-STALE (:686) |
| 5.2i | Arming check does not refuse missing W_MAX / telemetry | JUSTIFIED | PF3 T3.5 (modelled fallback, MINOR); D-ID-OK-LIMIT (:1480); "refuse to arm without eRPM" (R1) left to G7/G8 (:1492); report/04_limits.md 4.2 |
| 5.2j | Both rate modules startable by hand | CLOSED | PF3 T1.12 (refusal in module, McIndiRateControl.cpp:70); S3 sec. 2; T1.8 PARTIAL minor (vtol argv) |
| 5.2k | Held rate setpoint if publisher dies | CLOSED | PF3 T1.10; D-S3-SPTO (:373); MC_INDI_SP_TO; IndiRateSetpointWatchdogTest |
| 5.2l | mc_autotune starts with INDI | CLOSED | rc.mc_apps:31-38; PF3 T1.1; S3 sec. 5 |
| 5.2m | DShot driver freezes rpm without error or stale stamp | CLOSED | D-S3-FROZEN (:363); PF3 T2.frozen CLOSED for rate module, PARTIAL minor for pos module (bound written); IndiFrozenRpmTest |
| 5.2n | esc index = flag bit, pole count scales W_MAX, one stale motor kills measurement | CLOSED | PF3 T2.index CLOSED, T2.pole DEFERRED (calibration note), T2.online CLOSED |
| 5.2o | No INDI reset on rising edge of rates_enabled; no battery scaling | JUSTIFIED | PF3 T1.5 PARTIAL minor, T1.2 DEFERRED (D-PREFREEZE-R3 :839, reopen trigger written) |
| 5.3a | Hover noise source: ablation by signal substitution | OPEN | same as 2.2d (A-6) |
| 5.3b | G_T, k_cmd identified in hover only, R^2 0.34-0.93 | SUPERSEDED | redesign: g_t = g/ht from in-flight hover-thrust estimate, k_cmd 1, THR_MDL_FAC 1 (report/02_outer_loop_design.md:115; GATES.md:206); D-G1-DERIVE |
| 5.3c | No snap FF; differenced filtered jerk, measure FF value | CLOSED | D-A18-REOPEN, D-A18-SOURCE, D-JFF-SOURCE, D-JFF-OFFB, D-JFF-KEEP; results/g5_g55_s141_a18 |
| 5.3d | Sensitivity to GNSS latency and EKF velocity noise untested | CLOSED | G3 GNSS +-50 ms mismatch (D-OWNER-Q24); G4 profiles D-NOISE-PROF |
| 6.1 | Report is chronological, final controllers hard to find, stale text | CLOSED | report/01-04, A_history_errata.md (history appendix); g8_s247 checks (G8 itself still open) |
| 6.1b | Audit items: MC_RATE_CTL_TYPE cited, test counts, W1/W2 metric change, ratio quotes | SUPERSEDED | fresh report, archive untouched (F-4); archive-1..6 errata |
| 6.2 | Reviews checked report vs results, not raw logs | CLOSED | G1.3 two independent scripts (:84); two-key rule in GATES |
| 6.3, 10 | Agent management (process audit) | SUPERSEDED | fresh start F-4; process in MISSION.md, LESSONS.md, run_orchestrator.sh (weak: no row-level reading) |
| 7.g1 | Gate 1 evidence integrity | CLOSED | G1 PASSED S84 (GATE_STATUS.tsv) |
| 7.g2 | Gate 2 margins >= 6 dB, 45 deg, 2 periods + latency, 400 and 800 Hz | CLOSED | G2 PASSED freeze-10 (results/freeze10_s193/G2_SCORES.md) |
| 7.g3 | Gate 3 robustness, >= 300 runs, no LOC | JUSTIFIED | G3 NOT PASSED final (owner Q35 A, GATES "Owner amendment S243"); limits draw 3, draw 264 in report/04_limits.md |
| 7.g4 | Gate 4 noise, absolute limits from a real log | CLOSED | G4 PASSED freeze-10 (results/freeze10_s193/G4_SCORES.md); real-log part by F-3 (see 3.5a) |
| 7.g5 | Gate 5 modes, false maybe_landed, EKF reset, RC loss | JUSTIFIED | G5 PASSED with G5.6, G5.11 z, F-8 rows "not tested" by owner decision Q8(b) (GATE_STATUS G5 note) |
| 7.g6 | Gate 6 fallback to PID | SUPERSEDED | F-1 |
| 7.g7 | Gate 7 target hardware, bench, ident procedure | SUPERSEDED | F-3 (no target hardware); report/06_bringup_checklist.md; G6 outlook (G6 NOT PASSED item 7, results/g6_item7_s212/TALLY_S244.md) |
| 7.g8 | Gate 8 code: module tests, review items closed, safe defaults, docs | OPEN | the closure list is this file (needs owner/key acceptance); see g7_s249/G7_VERDICT_DRAFT.md; docs page pending G8 |
| 8 | Order of work and owner inputs | SUPERSEDED | MISSION.md stage plan; owner inputs voided by sec. 0 (F-3) |
| 11.1a | identify_g1 suspect (irregular rate, one-sample fit) | SUPERSEDED | D-G1-DERIVE (:221) G1 derived from airframe data, never regressed |
| 11.1b | ident_gt suspect (fit through origin) | SUPERSEDED | redesign g_t = g/ht (see 5.3b); D-IDENT (:626) |
| 11.1c | identify_g2 (stale rpm interpolation, wrong filter rate) | SUPERSEDED | D-G2Y-DERIVE (derive from rotor inertia) |
| 11.1d | ident_s8_delay (integer lags on cycle index) | SUPERSEDED | D-IDENT, D-ACTC-IDENT (:1317) output-error fit; ERPM_DLY calibrated (PF3 T2.timestamp) |
| 11.1e | accel_gain wrong (differentiates 59 Hz truth), carries report 8.10 attribution | SUPERSEDED | F-5 effort criterion dropped; D-EFFORT-BW; archive-6 |
| 11.1f | No self-test on any script | CLOSED | G1.4 (:85); D-IDENT-J (:643); self-test requirements (:640) |
| 11.2a | Run-to-run non-reproducibility from MAVLink/gz timing, commanded not applied | CLOSED | D-SCHED sim-time player (:107); D-A17 (:129); A-7 PARKED cause found; D-OWNER-Q8-Q15 applied-flag reference |
| 11.2b | eRPM drop generator fixed seed | CLOSED | JOURNAL.md:663 (seed fixed), :805 (drops per seed, G1.5 check 93e20fd849) |
| 11.2c | Gust drag uses world wind, not air-relative | OPEN | design/scenario_overrides_key_s110.md M-1 (injector has no vehicle velocity; fix or declaration not found) |
| 11.2d | Vibration added after IMU sample, no band limit, amplitudes unsourced | CLOSED | D-VIB-HOOK (:868); D-NOISE-PROF (:880); A-54 bound |
| 11.2e | Mass variant base link only; IMU-rate option changes physics step | CLOSED | D-SIM-STEP (:92, one physics step for all runs); bench_port_plan.md:55 model_variant |
| 11.2f | Ground truth stamped at reception | CLOSED | G1.2 (:83) |
| 11.3a | ~40 single-line mutations survive the 63 tests (test_review surviving mutations) | CLOSED | g7_s195/BREAK_AUDIT.md (66 mutations, 57 killed, 9 survivors) + SURVIVOR_TESTS.md + HELPER_SURVIVOR_TESTS.md; per-S-id mapping to test_review not written |
| 11.3b | Only closed-loop plant is roll-only, same model; no outer closed-loop test | JUSTIFIED | closed-loop evidence is SITL G2/G3/G5 on the full plant; unit scope per D-G7-HARNESS (:564) (weak) |
| 11.3c | Outer tests use level attitude only; wrong-way rotation would pass | JUSTIFIED | tilted flight in SITL (G5.5 offboard trajectories, G2 outer cells) would fail it; no unit row found (weak) |
| 11.3d | Measured-torque test inverts production formula with production allocator | OPEN | no record found; IndiMeasuredTorqueTest not shown to use an independent expected value |
| 11.3e | 8 untested behaviours (test_review sec. 4) | OPEN | g7_s249/G7B_TEST_INVENTORY.md: 4 MISSING (saturated-motor frozen rpm, pos esc age rule, omega_ff offboard-entry step, ERPM_TO predicate), 3 WEAK; the 7 ordered tests not written |
| 11.3f | Rate fixture can host a margin check | SUPERSEDED | margins measured in SITL (G2), D-G2-BREAK |

## Counts (92 rows)

| status | rows |
|---|---|
| CLOSED | 49 |
| JUSTIFIED | 12 |
| SUPERSEDED | 23 |
| OPEN | 8 |

## OPEN rows and proposed closure

- 2.2d / 5.3a (A-6, outer-loop hover command excess below 30 Hz): run the signal-substitution ablation on one hover log, or justify as a G4 absolute-limit pass (G4 PASSED, command RMS under 5e-4 floor) and report cause unknown as a limit.
- 3.4c (A-4, simulation speed factor): fly INDI step_roll seeds 1-3 at speed 1 and 4 (test already written in A-4), or report as a limit that all INDI evidence is speed 4.
- 4.6b (notch filters not mirrored on torque path): justify (SITL gz has no dynamic ESC notch, G2 measured at 267/400/800 Hz) and add one line to report/04_limits.md.
- 7.g8 (review closure list): accept this table at the G7 key; mark G7 row closed once the OPEN rows below are written.
- 11.2c (gust drag not air-relative): report as a limit (wind is a pure force, overstates drift disturbance) or pass vehicle velocity into `gust_x`.
- 11.3d (measured-torque test uses production formula): add one expected-value test with hand-computed numbers, or justify via the G2 measured-torque cells.
- 11.3e (4 MISSING + 3 WEAK behaviours): write the small tests (items 1-5 of the G7B ordered list) or justify each as glue/limit in the G7 verdict.
