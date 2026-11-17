# N2-A triage of pre-S36 anomalies (S66)

Method: read ANOMALIES.md rows, GATES.md (G1.6 lines 19-35, 49-52, 63, 80), DECISIONS.md:85-90, design/g16_s13.md,
design/determinism_s13b.md, JOURNAL.md entries, indi_project/results/v3_screen.md:20-24 and indi_project/ grep for c12.
Rows already carrying a PARKED mark (A-10, A-13, A-14, A-17, A-19) are re-checked, not re-decided. A-26, A-29, A-30 are S48+ and out of scope.

## Verdicts

| id | title | verdict |
|---|---|---|
| A-1 | Blend Tb 0.1 s lost altitude | PARKED |
| A-2 | PID hover effort spread 3.5x | CLOSED |
| A-3 | Sporadic vertical excursions in hover | PARKED (merged into A-14) |
| A-4 | INDI sensitivity to sim speed factor | OPEN stage 3, blocks G2 tables at speed 4 |
| A-5 | Failed v2 candidate c12 | ARCHIVE-ONLY |
| A-6 | Outer-loop hover excess < 30 Hz | OPEN stage 5 (kept per owner) |
| A-7 | Run-to-run non-reproducibility | CLOSED |
| A-9 | Yaw-rate ff double count | deferred to N2-B |
| A-10 | esc_status zero-dt pairs | PARKED (confirmed, keep) |
| A-13 | sensor_gyro single gaps | PARKED (confirmed, keep) |
| A-14 | EKF-truth z residual | PARKED (confirmed, keep) |
| A-15 | g1.1 truth rows gap | CLOSED |
| A-17 | arm/offboard instants spread | PARKED (confirmed, keep) |
| A-19 | truth-EKF yaw offset | PARKED (confirmed, keep) |

## Justifications

A-1 PARKED. Source v3_screen.md:22-24: single seed, pruned under O-12, hypothesis only (fast blend hands the low-frequency loop the
full motor gap while the failed motor saturates). The parameter still exists (mc_indi_rate_control_params.yaml:155, MC_INDI_ACT_BLD)
and the frozen default is 0.3 s, so the law is not gone, but no flown or planned scenario uses Tb < 0.3 s. Bound: Tb >= 0.3 s (default).
Reopen: any stage-4 identification or default change that proposes Tb < 0.3 s, or a motor-loss scenario. Closing test stays the stage 2
linear model with blend vs SITL at 0.1 and 0.3 s.

A-2 CLOSED with A-7. Cause: the 3.5x effort spread came from different slices of the flight in the window (A-7 / determinism_s11.md arm
time 15.37/17.57/17.54 s). With the sim-time player the window is anchored: GATES.md:30-35 (a1 triggers same sim time within 1 IMU
period, 15/15) and GATES.md:51-52 (30 runs, speed 1 and 4: effort spread <= 2.5 %, step delay <= 1.7 %). Hover effort at the noise
floor is covered by G1.6(b) recorded spreads.

A-3 PARKED. Evidence: g16_s13.md:69 the only excursion is s4 hover r5 max_dev 0.063 m, axis D, mid-window; D-SIM-SPEED overturn clause
(DECISIONS.md:89). Later work gives a mechanism: PID position loop holds the EKF height, so truth z error = EKF height error, A-14/A-20
bound <= 0.174 m (2/30 runs with 0.72 m initial baro bias, GATES.md:51-52). Not closed outright because no INDI hover was scored for it.
Bound: A-14 bound (truth z excursion <= 0.15 m in the hover window). Reopen: an INDI hover with a truth z excursion above the bound that
does not match the EKF height error. Closing test: plot truth z minus EKF z on the excursion run.

A-4 OPEN, stage 3, gate G2 (any G2 table flown at speed 4) and G6. Evidence read: the speed 1 vs 4 comparisons in GATES.md:51 and
g16_s13.md are PID; every INDI result found (g2_step_s64*, indi_vs_pid, JOURNAL.md:560) is speed 4 only. DECISIONS.md:89 explicitly
conditions the speed 4 choice on this. Test: INDI step_roll seeds 1-3 at speed 1 vs speed 4 with the player, difference within the
G1.6 same-seed spread. Can share the re-fly planned for A-30.

A-5 ARCHIVE-ONLY. c12 is a candidate in the first project (indi_project/results/s2_tuning/r1.md:16, indi_project/STATE.md:368:
v2 INDI r1, 1 failure in 240 flights, c12). The v2 law and tuning grid are not in the new modules; the row's own closing test says
close as obsolete once the v2 law is gone. Not explained from logs; no later work used c12. Not verified: I did not open the c12 flight logs.

A-6 OPEN, stage 5, gate G5 (outer loop, all modes). Signal-substitution ablation as written. No later evidence found in JOURNAL/STATE.

A-7 CLOSED (checked against G1.6 and the sim-time player). Cause identified S13: runner arm/offboard lag = 1 Hz HEARTBEAT phase, gz
free-running without lockstep (determinism_s13.md/_s13b.md). Resolved by the sim-time player: GATES.md:30-35 triggers exact (0 or
+1250 us, 15/15); GATES.md:49-52 and 80 (G1.6 table row): spreads equal at speed 1 and 4 over 2x15 runs, (c) differences with
stated sources, (d) in force; "provisional" mark lifted GATES.md:63. Residual: Commander tick (A-17 PARKED), A-14/A-19 PARKED.
Not resolved and stated: gz sensor-noise RNG seeding by --seed was never checked (determinism_s13b.md:120); bit-exact replay
is out of scope, the noise effect is inside the measured spreads. Reopen if a same-seed spread exceeds its G1.6(b) threshold.
Caveat: I read G1.6 results as quoted in GATES.md, not the g16_set_s32 README tables.

A-9 deferred to N2-B.

A-10, A-13, A-14, A-17, A-19: PARKED text present, bound and reopen trigger present in the rows. No change, except A-10 and A-13
have two status fragments and could be tidied.

A-15 CLOSED. Cause confirmed S20 (logger overwrite of queue-1 truth topics, log-poll flight), fix: sim-only topic sim_ground_truth
queue 16 (S21 T43: 7 gaps = gyro gaps, values equal truth). Close condition "g1.1 and metrics read the new topic and pass":
GATES.md:48/63 G1.1 provisional lifted; A-14 row states all tracking metrics use truth; remaining 7 gaps are A-13 (PARKED).
Not verified: I did not open a G1.1 table row for the truth gap criterion.

## Proposed replacement text

A-1 (ANOMALIES.md row, status) : PARKED S66. Bound: frozen Tb 0.3 s; Tb 0.1 s lost altitude in one seed of the first project (v3_screen.md:22), hypothesis: fast blend hands the low-frequency loop the full motor gap while the failed motor saturates. Not flown on the new module. Reopen if a stage-4 change or a motor-loss scenario uses Tb < 0.3 s; test: stage 2 linear model with blend vs SITL at 0.1 and 0.3 s.

A-2 (ANOMALIES_CLOSED.md): CLOSED S66 with A-7. The 3.5x PID effort spread came from the window covering different slices (arm time spread 2.2 s). With the sim-time player, effort spread <= 2.5 % over 2x15 same-seed runs at speed 1 and 4 (GATES.md G1.6, `results/g16_set_s32/speed{4,1}/README.md`).

A-3 (ANOMALIES.md): PARKED S66, merged into A-14. Only seen: s4 hover r5, 0.063 m, mid-window (`design/g16_s13.md:69`). Mechanism: the position loop holds the EKF height, so the truth excursion is EKF height error, bound 0.15 m (A-14). Reopen if an INDI hover shows a truth z excursion > 0.15 m not matching EKF z; test: plot truth z minus EKF z on that run.

A-4 (ANOMALIES.md): OPEN, stage 3, blocks G2 tables at speed 4 and G6. All INDI results are speed 4; the speed 1 vs 4 equality (G1.6) is PID only. DECISIONS D-SIM-SPEED is conditional on this. Test: INDI step_roll seeds 1-3 at speed 1 and 4 with the player; difference within the G1.6 same-seed spread (share with A-30 re-fly).

A-5 (ANOMALIES_CLOSED.md): ARCHIVE-ONLY S66. c12 is a first-project v2 tuning candidate (indi_project/results/s2_tuning/r1.md:16, STATE.md:368, 1 failure in 240 flights). The v2 law is not in the new modules; no later work uses it. Not explained from logs.

A-6 (ANOMALIES.md): OPEN, stage 5, gate G5 (outer loop all modes). Outer-loop hover command excess below 30 Hz, cause unknown. Closing test: signal-substitution ablation (truth accel / unquantised rpm / truth velocity). No later evidence found S66.

A-7 (ANOMALIES_CLOSED.md): CLOSED S66 (with A-2). Cause: runner arm/offboard lag = 1 Hz HEARTBEAT phase, gz free-running (`design/determinism_s13*.md`). Sim-time player: triggers exact within 1 IMU period 15/15; spreads equal at speed 1 and 4 over 2x15 runs; G1.6 (a1)(a2)(c)(d) met, GATES.md:30-35, 49-52, 80. Residual: Commander tick (A-17), A-14, A-19. gz noise seeding by --seed unchecked. Reopen if a same-seed spread exceeds its G1.6(b) threshold.

A-15 (ANOMALIES_CLOSED.md): CLOSED S66. Cause: logger overwrite of queue-1 truth topics (S20 log-poll flight). Fix: sim_ground_truth, queue 16 (S21 `results/a15_s21/README.md`): remaining 7 gaps equal the gyro gaps (A-13, PARKED); metrics read truth, G1.1 provisional mark lifted (GATES.md:63).
