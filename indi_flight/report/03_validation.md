Status: draft complete

# Chapter 3. Validation against the gates

Gate G8 requires design first, then validation against the gates. Chapters 1 and 2 give the design (inner and outer
loop); this chapter reports the gates that are PASSED (G1, G2, G4, G5) and the two that are NOT PASSED (G3, G6),
stated with their data. G7 is not reported here (section heading only). Every number below comes from a gate evidence file and is copied from
it, not recomputed. G1, G2, G4, G5 and the S199 G3 campaign were flown on FREEZE-10 (D-FREEZE-10, firmware
7fe6206fcc); the S213 G3 re-fly, G3 route B and G6 item 7 were flown on gate binary 903eae63 (FREEZE-10 plus the simulator
bridge fix f110361a33, D-BINARY-GZFIX). The G3 candidate fixes (i)-(iii) were rate-loop variants flown on their own
builds and are not part of any shipped firmware. Freeze discipline: a later firmware change re-flies the rows it invalidates, so a
verdict here holds for that firmware only. PID values are a reference and never a pass condition (F-5).

Citations: `GATES.md` = `indi_flight/GATES.md` (section title in quotes), `GS` = `indi_flight/GATE_STATUS.tsv`, `F10` =
`indi_flight/results/freeze10_s193/`. Evidence paths are relative to `indi_flight/` unless they start with `F10`.
Configuration common to G2, G4, G5: reference airframe quad5in (`4040_gz_quad5in`), FREEZE-10 firmware 7fe6206fcc
(binary built 2026-11-21 22:38), INDI stack, simulation provenance recorded per run (G1.7). Controller rates are stated per gate.

## 3.1 G1 Evidence integrity

State: PASSED S84 (`GS` row G1; `GATES.md` "G1 FINAL (2026-11-16, s36)", paragraph "G1 PASSED (S84, 2026-11-18)").

What it tests. G1 does not test the controller; it tests that the evidence can be trusted. Items G1.1 to G1.7 (logger
completeness, truth topics stamped in sim time, two scoring keys, self-test break-checks, injector checks, mode-change
timing, run provenance). Owner answers Q2 to Q4 (S50) amended the text: G1.1 is logger completeness (every published
sample logged, <= 0.1 % missing); mode-change response spread <= 10 ms and latency <= 20 ms (Q3-A); G1 frozen with
its evidence limits (Q4-A). The passing condition set by the owner at S50: G1.7 implemented and its runner check
break-tested.

| item | state | evidence |
|---|---|---|
| G1.1 | met under Q2-A: logger completeness -0.014 %, sim holes 0.012 % of steps, single holes <= 6.3 ms; fails the original gap rule on simulator holes (A-13) | `GATES.md` "G1 FINAL", table |
| G1.2 | met (truth topic stamped in sim time) | same |
| G1.3 | met (two keys, atan2 attitude angle in both) | same |
| G1.4 | met (self-tests break-checked) | same |
| G1.5 | deferred per injector: each injector and plant variant is checked before its first campaign | same |
| G1.6 | (a1) met; (a2) spread within one Commander period (10 ms), latency within two; (b) spreads recorded; (c) met; (d) in force | same; `results/g16_set_s32/speed{4,1}/README.md`, `results/a20a19_s35/README.md` |
| G1.7 | implemented S50 (`bench/provenance.py`, `run_scenario.py --gate`): run.json records commit, clean-tree flag, SITL binary hash, sim model hashes, param hashes; the runner refuses a dirty tree or a stale binary. Refusal break-tested | `GATES.md` "G1 PASSED (S84)" |

Reproduce: self-test `bench/tests/test_provenance.py` (S84: ALL PASS, covering dirty tree, stale binary, header newer,
missing input and missing binary refused) (`GATES.md` "G1 PASSED (S84)"). G1.1 per run: `bench/gate_g1.sh`.

Evidence limits carried by every later verdict (`GATES.md` "G1 FINAL", numbered list):
1. Holes: two kinds, reported per run (sim holes in `sensor_gyro` / `sim_ground_truth`; controller holes in
   `vehicle_angular_velocity` / `actuator_motors`). More than 0.1 % holes in a run means re-fly that run, not a gate failure.
2. Commander tick (Q3): spread <= 10 ms, latency <= 20 ms; analysis windows anchor on the logged transition.
3. EKF-truth height (A-14) <= 0.15 m in hover windows; position-hold spread <= +-0.15 m.
4. EKF heading error (A-19) <= 1.6 deg, constant within a hover: no yaw threshold below 1.6 deg on truth.
5. Bench parameter sets carry SENS_BAR_AUTOCAL 0 (A-20) and the logger poll `-p actuator_motors` (S16).

G1.5 stays deferred per injector; it is not a failed item.

## 3.2 G2 Stability margins

State: PASSED at FREEZE-10, S194, 2026-11-22 (`GS` row G2; `GATES.md` "G2 verdict at freeze-10 (S194, 2026-11-22)").
Earlier: freeze-7 and freeze-8 NOT PASSED, freeze-9 PASSED S184.

What it tests (`GATES.md` "G2 Stability margins, measured", "G2-STEP", amendments Q13, Q16, Q19 in the owner amendment sections).
Margins of the open loop L measured in flight by multisine injection (1-60 Hz, hover): rate roll, pitch, yaw with INDI
break point M3a; attitude, velocity, position and outer acceleration loops by their own break points. Design of the
measurement and the model cross-check: `report/g2_margins.md`.

| quantity | threshold | source |
|---|---|---|
| phase margin PM | >= 45 deg | `GATES.md` G2 "Pass" |
| gain margin GM | >= 6 dB (n/a where there is no -180 deg crossing in 0.2-8 Hz; plateau GM from key 2 also reported) | `F10/G2_SCORES.md` Limits |
| delay margin DM | >= 2 control periods + telemetry latency (never binding in the evidence) | same |
| Q13 A | bins with |L| > 1 within 10 deg of -180 deg are gain-reduction margins 20 log10 |L| and must also be >= 6 dB | same |
| key agreement (second key) | |dPM| <= 3 deg and |dGM| <= 1 dB, same presence or absence of a GM | same |
| holes | per-run hole report PASS (G1 limit 1) | same |
| G2-STEP, every seed | roll/pitch overshoot <= 5 %, 2 % settle <= 450 ms; yaw overshoot <= 5 %, settle <= 1350 ms; truth overshoot <= 5 % | `GATES.md` "G2-STEP" |

G2-STEP thresholds are absolute (F-5). Their derivation used the PID reference of S61, seeds 1-3: roll/pitch overshoot
0 %, settle max 412 ms; yaw overshoot <= 0.3 %, settle max 1240 ms (`GATES.md` "G2-STEP").

Configuration flown. Outer loops: 24 cells at FREEZE-10 (3 axes ax1-ax3, break points pt0 and pt1, controller rates 400
and 800 Hz, 2 seeds), spot cells: rate roll `roll800_fwdef_s2` and attitude pitch `ax2_r400_s1`. G2-STEP: 3 seeds x
roll, pitch, yaw. 267 Hz is reported, not a pass condition; 250 Hz is not measured (`GATES.md` "G2 verdict at freeze-10").

Result (`F10/G2_SCORES.md`, outer table, spot table, G2-STEP table, section "Re-score S194"):

| item | worst case | limit | cell | evidence |
|---|---|---|---|---|
| outer PM, key 1 | 49.1 deg | >= 45 | pt0_ax2_r400_s2 | `F10/G2_SCORES.md` "Totals" |
| outer xy GM | 13.5 dB | >= 6 | pt0_ax1_r400_s1 | same |
| outer plateau GM (key 2) | 12.88 dB | >= 6 | pt0_ax2_r400_s1 | same |
| outer DM | 229 ms | not binding | pt1_ax3_r800_s1 | same |
| outer margins | 24/24 meet limits | | | same |
| holes | 24/24 PASS after one re-fly (pt1_ax2_r400_s2) | | | "Re-score S194" |
| key 2 agree | 21/24; 3 BLOCKED, see limits | | | same |
| spot, rate roll800_fwdef_s2 | GM 15.7 dB, PM 46.9 deg, DM 75.5 ms, holes PASS | PM >= 45 | | "G2 spot-check cells" |
| spot, attitude ax2_r400_s1 | GM 13.7 dB at 4.29 Hz, PM 48.0 deg, DM 93.5 ms, holes PASS | PM >= 45 | | same |
| G2-STEP | 9/9 PASS both keys | | | "G2-STEP" |
| step worst roll/pitch overshoot | 0.65 % | <= 5 % | roll s3, pitch s1 | same |
| step worst roll/pitch settle | 347.5 ms | <= 450 ms | pitch s2 | same |
| step worst yaw overshoot | <= 0.17 % | <= 5 % | | same |
| step worst yaw settle | 1196.25 ms (89 % of limit) | <= 1350 ms | yaw s3 | same |

Comparison with freeze-9 in the same file: worst xy PM 49.1 deg (freeze-9 min 48.5), worst xy GM 13.5 dB (freeze-9 min
13.4), worst DM 229 ms (freeze-9 min 231 ms). The hole re-fly cell passed with PM 56.9 deg, GM 13.9 dB, DM 0.485 s
(original run PM 59.59, GM 13.83, hole FAIL: one 22.50 ms setpoint gap, excess 11.25 ms above the 10 ms limit; the
original is kept in `F10/g2o/orig_s194/`).

PID reference: for G2 the evidence file gives only the G2-STEP derivation values above; the table of margins has no PID column.

Evidence limits (`GATES.md` "G2 verdict at freeze-10"; `F10/G2_SCORES.md`):
1. Key 2 is BLOCKED on 3 cells on key agreement only; both keys are above the limits in each: pt1_ax1_r800_s1 (PM 71.3 key 1
   / 67.8 key 2, dPM -3.48), pt1_ax3_r400_s2 (PM 58.7 / 58.2; GM present in key 2 only, 16.3 dB), pt1_ax3_r800_s2 (GM
   22.4 key 1 / 17.8 key 2, dGM -4.6). Not re-flown (owner decision). Clean cells (holes PASS and key agreement): 21/24.
2. Rate and attitude spot margins are thin: PM +1.9 deg and +3.0 deg above 45. The attitude spot cell has a second -180 deg
   crossing at 0.237 Hz with |L| = 7.3, read as a gain-reduction margin of 17.3 dB under Q13 A; read literally as a signed
   minimum the scorer prints -17.31 dB (the evidence file asks the owner to rule on this; the gate verdict uses the Q13 A reading).
3. Three rate cross-check groups and A-51 stand as Q16 A. No second key on the spot cells. 250 Hz not measured.

Reproduce (all from the repo root, host python3; `F10/G2_SCORES.md` section "Commands run"):
- outer table: `g2_freeze_table_s163.py` with the folder rewritten to `freeze10_s193/g2o` (`sed` as in the file);
- key 2: `bench/g2_key2_outer_s164.py` with the same rewrite, writes `g2o/key2.md`;
- G2-STEP: `python3 indi_flight/bench/g2_step_metrics.py steps/g2_step_primary.json steps/seed{1,2,3}/step_{roll,pitch,yaw}_indi`
  and key 2 `bench/t127_step_metrics_key.py steps/seed<N>/step_<axis>_indi steps/key2_seed<N>_<axis>.md`;
- flights: `bash indi_flight/results/freeze10_s193/queue.sh 4` (queue step 4).

## 3.3 G3 Robustness

State: NOT PASSED, final (owner answer Q35 A, S243). The G3 chain stops: no re-fly and no new firmware route
(`GATES.md` "Owner amendment S243", `GS` row G3).

What it tests. A robustness campaign of 300 valid simulated flights of 100 s, 240 Latin-hypercube draws plus 60 corner
runs (corners C1-C6, 10 runs each), each flown as arm, take-off, hover, roll steps, lemniscate trajectory, hold with a
gust or fault. Factors: controller-versus-plant gain error x0.5-2 per axis, motor time constant x0.5-3 and up/down
asymmetry, added delay 0-10 ms, mass and inertia +-30 %, thrust sag, weak motor, telemetry faults, vibration, GNSS latency,
wind (`GATES.md` "3. G3 Robustness campaign", factor table). Pass items per run: 1 no LOC (loss of control), 2 no sustained
oscillation, 3 steady state, 4 tracking (lemniscate horizontal RMS <= 0.5 m), 5 recovery after the event, 6 rate-mode hold.
Campaign pass: 0 LOC, 0 oscillation, items 3-6 in every valid run, no quota (S208 Q27). PID is flown on the same draws as
a reference only.

History of attempts (all NOT PASSED):

| attempt | result | evidence |
|---|---|---|
| S199, freeze-10, 300/300 flown | item 1 FAIL: run 245 (C1) 2 Hz pitch divergence, run 264 (C3) tilt > 60 deg at the fault; item 2 FAIL on 79 of 297 scored runs; item 3 94.95 % | `GATES.md` "G3 verdict at freeze-10 (S199...)"; `results/g3_campaign_f10/` |
| S213, re-fly with drawn controller ACT_TC (actuator time-constant parameter), halted | run 022 (draw 262) item 2 not reproduced at speed 1, not counted; run 024 (draw 264, C3) LOC at 60.78 s (speed 4) and 61.03 s (speed 1), ACT_TC 0.0177 | `GATES.md` "G3 verdict, re-fly with drawn controller ACT_TC (S213...)"; `results/g3_refly_actc_s212/` |
| S231-S236, candidate fixes (i) ACT_BLD 0.10, (ii) MAP_TC 0.2, (iii) rate integrator | all MISSED the pass line on both keys. (i) 264 items 1+2, 262 item 2; (ii) LOC on the joint draw and 264; (iii) LOC 264, item 2 on 262 | `GS` row G3; `results/g3_cand_i_s231/`, `g3_cand_ii_s233/`, `g3_cand_iii_s235/SCORES.md` |
| S242, route B (300 fail-fast, binary 903eae63), halted at run 003 | draw 3 item 2 FAIL; item 4 fails on draws 2 and 3 | `GATES.md` "G3 verdict, route B (S242...)"; `results/g3_routeB_s239/HALT_S240.md`, `REF_S241.md` |

Key failing draws.
- Draw 3 (route B, slow motors, tau x2.4-2.8): INDI q (pitch rate) line at 2.00 Hz, sustained, both scoring keys,
  reproduced at speed 1. PID on the same draw and seed passes item 2 (`REF_S241.md`). Local q PSD peak 2.0-2.25 Hz,
  about 30 dB above PID (`GATES.md` "Owner amendment S243"). INDI-specific.
- Draw 264 (corner C3: thrust scale 0.351, motor 3 at 0.709, mass 1.3): INDI tilts past 60 deg at the fault, in
  freeze-10 (60.67 s speed 4, 60.91 s speed 1, ACT_TC 0.033) and in the re-fly (ACT_TC 0.0177). PID flies the draw
  without LOC (tilt max 40 deg). INDI-specific (`GATES.md` S213 verdict). Not changed by ACT_TC.
- Item 4, draws 0, 2, 3 (INDI / PID, limit 0.5 m): 0.418 / 0.768, 0.834 / 0.862, 0.553 / 0.917 m. PID fails too, and INDI is
  not worse, so under the PID guard (Q35 C) these rows are a test defect, not counted against INDI. One flight per stack
  and draw, no spread estimate (`GATES.md` "Owner amendment S243").
- Item 5 reading A and B (Q34): re-score of the S230 pre-test matches the owner's 6/6 events
  (`results/g3_pretest_s230/Q34_KEY1.md`, `Q34_KEY2.md`). Serves this write-up only, not a new campaign.

Verdict. G3 is NOT PASSED for this project. Only 25 runs (S213) and 3 runs (route B) of the re-flies were flown before
the halts, so the 300-run result is not available for any firmware after freeze-10.

Limits carried to the report (measured, with the data above):
1. Slow-motor 2 Hz pitch mode (draw 3): INDI-only, PID passes.
2. Draw 264 LOC (saturation plus weak motor): INDI-only. The cause was not traced to its origin (`GATES.md` "Owner
   amendments S208", item 4).
3. Item 4 tracking above 0.5 m on draws 0, 2, 3 in both stacks (PID guard, not counted).
Hypothesis, UNVERIFIED: actuator-model mismatch (motor tau x2.4-2.8 of nominal against MC_INDI_ACT_TC 0.033)
(`GATES.md` "Owner amendment S243"). No evidence file shows it. The draw 264 failure does not depend on ACT_TC.

Reproduce: route B draw 3 re-fly, `indi_project/docker/run.sh -n g3c_s241_003 -t 1500 -- python3 indi_flight/bench/g3_run.py
--seed 173 --n 300 --start 3 --stop 3 --base-params indi_flight/results/g5_freeze_s157/params.params --out-root <dir>
--timeout-s 1200 --speed 1`; PID reference `python3 indi_flight/results/g3_routeB_s239/ref_s241/fly_pid_ref.py 3`
(`results/g3_routeB_s239/REF_S241.md`). Campaign form: `bench/gate_g3.sh pretest | campaign N SEEDFILE` (`GATES.md`
definition, not run for this write-up).

## 3.4 G4 Noise and effort

State: PASSED at FREEZE-10, S194, 2026-11-22 (`GS` row G4; `GATES.md` "G4 verdict at freeze-10 (S194, 2026-11-22)").
Earlier: freeze-7 and freeze-9 NOT PASSED; freeze-9 PASSED under Q20 (S187).

What it tests (`GATES.md` "### 4. G4 Noise and effort"). Three noise profiles (quiet, typical, harsh), flights hover
and cruise, 3 seeds: 18 INDI runs. Metrics: R20 = rotor-speed ripple RMS (20 Hz high-pass), R4 (4 Hz), C20 command RMS
(`bench/a11_effort_rate.py`), clip fraction (share of samples at command 0 or 1). Additional rows: G3 items 1-3 hold
on the harsh profile in hover (item 1, item 2 sustained-oscillation detector, item 3 steady state); no sustained 20-100 Hz
chatter on the command.

| quantity | quiet | typical | harsh | source |
|---|---|---|---|---|
| R20 | <= 1 % hover | <= 1.5 % | <= 3 % | `GATES.md` section 4 table |
| C20 | <= 0.004 | <= 0.006 | <= 0.012 | same |
| R4 | <= 3 % | <= 4 % | <= 6 % | same |
| clip fraction | 0 | 0 | <= 0.1 % | same |
| cruise R20 and C20 | hover limit x 1.5 | | | same; R4 and clip not scaled (`F10/G4_SCORES.md`) |

Amendments applied (owner answers): Q14 A chatter = a 20-100 Hz command line with peak > 20 x median and RMS >= the
flag limit (5e-4); Q15 A and Q19: windows overlapping the 3 s after a nav_state change are skipped by the item 2 detector;
Q18 A: windows overlapping [ground_contact - 1 s, landed + 1 s] skipped; Q20: PID guard on skipped windows, a
transition is checked only where the INDI skipped window is flagged (ratio > 20 and narrow RMS >= 5e-4), FAIL if INDI
narrow RMS > 1e-3 or the line is INDI-only (`GATES.md` "Owner amendments S187"). The scope of item 2 is harsh hover;
harsh-cruise rate flags are informational (S183 amendment).

Configuration flown: 18 INDI re-fly runs `g4/{hover,cruise}_{quiet,typ,harsh}_s{1,2,3}` at FREEZE-10, queue step 3
(`F10/G4_SCORES.md`). PID references for the Q20 guard: freeze-9 flights `freeze9_s183/g4_pid` (hover_harsh and
cruise_harsh s1, s2); the PID path is unchanged by the freeze-10 commits.

Result (`F10/G4_SCORES.md`, "Summary" and "Effort" tables):

| item | worst case or count | limit | evidence |
|---|---|---|---|
| effort R20, C20, R4, clip | 18/18 PASS | | "Summary" |
| key 1 (effort, item 1, chatter, item 2) | 18/18 PASS | | same |
| key 2 | 18/18 PASS, no key disagreement | | same, "Integrity" |
| hover_harsh R20 / C20 / R4 / clip | 0.016 % / 0.00025 / 0.041 % / 0.0000 | 3 / 0.012 / 6 / 0.001 | "Effort" |
| cruise_harsh R20 / C20 / R4 | 0.023-0.024 % / 0.00065-0.00067 / 0.271-0.295 % | 4.5 / 0.018 / 6 | "Effort" |
| chatter, K1 nearest to limit | 4.12e-04 (cruise_harsh_s2) | flag 5e-4 | "Noise", HEAD verdict |
| hover item 3 (xy RMS / mean dz), harsh | 0.027-0.047 m / -0.029 to +0.013 m | 0.15 m / 0.1 m | "Noise" |
| Q20 guard | 54 transitions per key, 0 checked, 0 FAIL, max INDI narrow RMS 3.459e-04 | 5e-4 flag, 1e-3 bound | "Q20 PID guard" |
| guard self-tests | key 1 8/8, key 2 9/9 | | same |

PID reference values: the Q20 guard reports INDI and PID narrow-band RMS at the same transition only at freeze-9
(for example 17->4: INDI/PID 2.94/3.78, 4.84/4.28, 4.47/3.93, 2.86/3.88 e-4, ratio 0.78-1.14; `GATES.md` "G4 verdict at
freeze-9 under Q20"). At FREEZE-10 none reached the 5e-4 floor, so none was checked.

Evidence limits (`GATES.md` "G4 verdict at freeze-10"; `F10/G4_SCORES.md`):
1. Harsh-cruise rate flags are informational (S183).
2. Item 3 on cruise is not part of the G4 verdict: it FAILS 9/9 cruise rows (9/18 overall) in the scorer, the same as
   freeze-9 (6/9). The mean |dz| 0.135-0.333 m (freeze-9 0.10-0.22) is read in a window after AUTO_LAND, both stacks (RECONCILE_S180
   task 2); it is not a G4 row. Shown per row so the owner can decide.
3. The Q20 guard has a PID side only for hover_harsh and cruise_harsh s1, s2, from freeze-9 flights.
4. The 20 Hz take-off to loiter transient exists in both stacks at 0.05 % of full command (freeze-9 verdict).

Reproduce: `bench/gate_g4.sh profile flight seed` (`GATES.md` section 4); Q19 scoring `g4/rescore_key1_q19.py` and key 2;
Q20 guard `bench/g4_guard_q20_key1.py` and `bench/g4_guard_q20_key2.py` (each with a synthetic self-test); flights by
`F10/queue.sh` step 3.

## 3.5 G5 Modes and transitions

State: PASSED at FREEZE-10, S198, 2026-11-22 (`GS` row G5; `GATES.md` "G5 verdict at freeze-10 (S198, 2026-11-22)").

What it tests (`GATES.md` "### 5. G5 Modes and transitions"): rows G5.1 to G5.11 on the INDI stack, 3 seeds per row, two
keys where a second script exists. Amendments applied: Q8 (S175: G5.6 and G5.11 z not tested; G5.8 at 3 m/s excursion definition,
add.3 (i)), Q10 B (G5.2 settle band max(2 %, 0.10 m)), Q12 B (G5.11 ekf_xy judged on truth excursion <= 0.5 m, tilt jump
reported only), Q17 A (G5.10 stabilized full-scale), Q21 (G5.10 SAT part), Q25 B (G5.5 limit H_lim = max(0.5 m, tau_att x
v_rms), tau_att = 1 / MC_ROLL_P = 0.125 s; `GATES.md` "Owner amendments S197"). The PID flight is a reference only.

Configuration flown: all flights on the FREEZE-10 binary (7fe6206fcc), INDI stack, `F10/g5/`, `F10/g5_modes/`, `F10/g55/`,
`F10/events/`, `F10/g510_stab/`; events seeds 2 and 3 and G5.8 at 3 m/s flown at S198 on the same binary
(`F10/g5_gaps_s198/README.md`: HEAD differs only by unit tests and the one-line `IndiStageMode.hpp` fminf/fmaxf change e9e85e395d, same arithmetic).

Result per row (`F10/G5_VERDICT_AUDIT.md` row table; rows complete at S198 per `GATES.md` verdict):

| row | limit | result | key 2 |
|---|---|---|---|
| G5.1 acro | RMS rate error <= 10 deg/s on 100 deg/s steps; no LOC | 3/3, worst 1.94 | PASS 3/3 |
| G5.1 stab | tilt <= 3 deg, yaw rate <= 10 deg/s after release | 3/3, worst tilt 0.12 | PASS 3/3 |
| G5.2 altctl z | overshoot <= 0.3 m, settle <= 4 s | 3/3 | PASS 3/3 |
| G5.2 posctl xy | x overshoot <= 0.5 m, settle <= 4 s | 3/3 | PASS 3/3 |
| G5.3 hold | 3-D RMS <= 0.3 m in 5 m/s wind | 3/3, worst 0.062 | PASS 3/3 |
| G5.3 mission | 4 waypoints within 1.0 m | 3/3, worst 0.970 m (margin 0.03 m) | none exists |
| G5.4 take-off, land | overshoot <= 0.5 m, edge step <= 10 %, dip <= 0.3 m, td vz <= 0.8, tilt <= 10 | 6/6 | auto_land10 3/3; take-off in auto_tour not key-2 scored |
| G5.4 RTL | height error <= 1 m | 3/3, 0.045-0.062 m | none |
| G5.5 o1-o7 | H RMS <= H_lim (Q25 B), V RMS <= 0.3 m | 21/21 under Q25 B (as written 20/21: o2 s1 0.5027 > 0.5) | 21/21 |
| G5.5 offb_vel_step | vx RMS <= 0.2, end vx <= 0.1, dz <= 0.3 | 3/3 | 3/3 |
| G5.7 mode switch | thrust step <= 20 %, attitude jump <= 5 deg | 3/3, worst 3.98 deg | 3/3 (freeze-9: 3/3 FAIL) |
| G5.8 hover rc, link, offboard loss | entry <= 1 s after timeout, excursion <= 1 m | 9/9, entry <= 0.51 s, excursion <= 0.121 m | PASS (entry only for link, offboard) |
| G5.8 at 3 m/s | same, excursion from the commanded setpoint (Q8 add.3 (i)) | 9/9, excursion 0.16-0.25 m, hold entered on every event | PASS, keys within 0.012 m |
| G5.9a kill | motors 0 within 1.25 ms of the kill rise | PASS, 0.00-1.25 ms | PASS on the gate definition |
| G5.9b re-arm states | all INDI states zero | PASS | values zero |
| G5.9c first second | command change <= 5 % of full scale | <= 0.01 % | 0.93-1.02 % |
| G5.9d take-off after re-arm | handover step <= 10 % hover, dip <= 0.3 m | 4.0-4.7 %, dip 0 m | PASS |
| G5.10 stabilized full-scale | no LOC; tilt <= MPC_MAN_TILT_MAX + 5 deg; att err <= 5 deg 1 s after centre | 3/3 (tilt 35.50, err 0.24) | 3/3 |
| G5.11 ekf_yaw | excess <= 1 deg over no-event p95; excursion <= 0.5 m (`F10/G5_SCORES.md:160`) | 3/3 (s2 excess -0.33 deg, s3 +0.12 deg, s3 excursion 0.040 m) | see limits |
| G5.11 ekf_xy | truth excursion <= 0.5 m, no oscillation (Q12 B; `F10/G5_SCORES.md:160`) | 3/3, 0.234-0.248 m | excursion PASS |
| F-7 | edge step <= 10 % of hover in every take-off | no thrust step at ramp to flight edge | |

Worst-case details (`F10/G5_5_RESCORE_Q25.md`): G5.5 worst INDI margin to H_lim o1 +0.049, o2 +0.066, o3 +0.043, o4
+0.079, o5 +0.456, o6 +0.449, o7 +0.052 m; o2 H_lim is 0.5685 m (reference speed RMS 4.548 m/s over the scored window),
the lemniscate rows 0.500 m floor (reference speed RMS 3.711 m/s gives 0.464).

PID reference values: G5.8 at 3 m/s seed 1 PID excursion 0.46-0.51 m (0.479, 0.514, 0.458 in
`F10/g5_gaps_s198/moving/G58_KEY1.md`) against INDI 0.16-0.25 m; both pass the 1 m limit. The G5.10 PID flight is a
reference, freeze-9 PID kept (`F10/G5_VERDICT_AUDIT.md`).

Evidence limits (`GATES.md` "G5 verdict at freeze-10"; `F10/G5_VERDICT_AUDIT.md`; `F10/g5_gaps_s198/README.md`):
1. Mission (G5.3) and RTL (G5.4) have key 1 only: no key-2 script exists, as at freeze-9. Mission waypoint margin 0.03 m.
2. Not tested: G5.6 and G5.11 z reset (owner Q8(b), S175); accel-only offboard and take-off on an offboard setpoint
   alone (owner decision F-8).
3. G5.10 SAT part dropped (Q21): no stack reaches 4 motors >= 0.99 for 1 s (`results/g510_q21_s187/`: INDI max motor 0.869, PID
   aborted); saturation under the position loop stays covered by G3 C3.
4. Key 2 quirks, read on the gate definitions: G5.9a key 2 prints FAIL on the legacy switch reference (+6.25 / +10.0 ms),
   but the kill-rise reference gives 0.00 ms; G5.9b and G5.9c key 2 print no verdict, values inside the limits; G5.11 key 2
   does not compute oscillation and applies a legacy 1 deg tilt rule that Q12 B removed for xy; s3 raw ekf_yaw jump 1.003 deg
   (excess 0.06 deg).
5. The G5.5 as-written failure (o2 s1 0.5027 vs 0.5) falls under the Q25 B limit; the audit notes the amendment expected 0.62,
   the scorer uses 0.5685.
6. The G5.8 3 m/s scorer is new at S198 (`bench/g58_moving_check.py`, self-test `bench/tests/test_g58_moving_check.py`, 5 tests).
   Link-loss entered hold on all three seeds in the new scorer.

Reproduce: events `python3 indi_flight/bench/g5_events.py --controller indi ... --seed N --params ... --out events/g5_events_sN`
(moving: add `--moving`); scoring `g5_rows_check.py`, `g511_check.py`, `g5_rows_key2.py`, `key2_g511` (copy for seeds 2, 3);
G5.8 3 m/s `python3 indi_flight/bench/g58_moving_check.py RUN_DIR --out FILE`; outer flights `F10/queue.sh` (`F10/g5_gaps_s198/fly.sh`
for the gap flights). Per-row key-1 and key-2 outputs are listed in `F10/G5_VERDICT_AUDIT.md`.

## 3.6 G6 Defaults and identification

State: NOT PASSED (S244, `GS` row G6; `GATES.md` "G6 item 7 verdict (S244...)").

What it tests. G6 starts from wrong physical parameters (x2 and x0.5 on mass, inertia, motor tau, thrust constant: 8
single-parameter starts plus the all-high and all-low corners), runs the shipped identification chain once, loads the
identified values with no other edit, and then must pass G2 (stability margins), G3 (robustness) and G5 (modes and
transitions) (`GATES.md` "6. G6 Defaults and identification from a wrong start"). Item 7 (S208 Q27, reduced by S211b
Q29): the 60 corners C1-C6 flown un-identified (`MC_INDI_ID_OK` 0, gains x0.5, ACT_TC 0.05). Pass: item 1 (no LOC) in every
valid run; item 2 only inside the identification-manoeuvre window; the rest reported. The ~100 Latin-hypercube runs were
dropped, so that coverage is a stated limit.

Result.
- G3 is final NOT PASSED (S243), so G6 cannot pass: it requires G3 (`GATES.md` "Owner amendment S243", G6 consequence).
- Item 7, runs 240-299 (gate binary 903eae63), both keys: item 1 FAILS. LOC in runs 278 and 295 (both keys). Runs 262
  (altitude loss), 264 (height < 0.3 m), 269 and 292 (tilt > 60 deg) were stopped by the flight watchdog. The chain marked
  them invalid, but a watchdog stop is not in the list of harness aborts, so they count as LOC: 6 LOC in 58 runs.
- Invalid (harness): 274 (wall timeout), 284 (no INDI status in the log), not re-flown (cannot change the verdict).
- Reported, 54 runs scored in the tally (key 1 / key 2 fails): item 2 over the whole run 21 / 22, item 3 2 / 2, item 4
  18 / 18, item 5 30 / 30, item 6 0 / 0. Overall pass 12/54 on both keys (`results/g6_item7_s212/TALLY_S244.md`).
  Run 240 item 5 was scored before the Q34 key change; per-corner failures are not reported (no run-to-corner map).
- Identification quality: ACT_TC identification error 0 of 30 cells failed in the SITL grid (r_mean 0.899-1.002); time
  constants within 3.7 %, delay offset about +1.75 ms; inert frames factor, quad5in plant only, one seed mostly
  (`results/actc_grid_s209/README.md`; the telemetry-instance bound is `REFIT_INST0.md`, not read here).
- Outlook flights (stock x500, a vehicle of about 1 kg, one above 5 kg) are reported only and not a pass condition. They
  have not been flown yet (last project step), so nothing is reported here.
- Item 2 over the whole run is reported only; it is not the item 2 pass window and the window-limited score does not exist.

Verdict. G6 is NOT PASSED: G3 final NOT PASSED, and item 7 fails item 1 (6 LOC in 58 runs). The identification
procedure and the defaults evidence stay in the report as the method and its limits.

Reproduce: tally `bash indi_flight/bench/g3_chain.sh rescore indi_flight/results/g6_item7_s212` (it rescored 0 runs, the
tally uses the stored scores; `results/g6_item7_s212/TALLY_S244.md`). ACT_TC grid `python3 indi_flight/bench/actc_grid.py
--out indi_flight/results/actc_grid_s209`, table `python3 indi_flight/bench/actc_grid_table.py`
(`results/actc_grid_s209/README.md`). The definition's `bench/gate_g6.sh start_id` does not exist in `bench/`.

## 3.7 G7 Code

pending: see GATE_STATUS.tsv

## Unverified

- `report/g2_margins.md` was only cited for method; its S-era margin tables were not compared with the FREEZE-10 values. [open: not compared]
- G5 rows G5.1-G5.7 results come from the audit table written S197 before the S198 gap flights; the S198 verdict says they are unchanged. [open: needs re-read of the S197 audit versus S198 verdict]
- Reproduce commands for G1.1 (`bench/gate_g1.sh`) and G4 (`bench/gate_g4.sh`) come from `GATES.md` definitions, not from the FREEZE-10 evidence; the S193 G4 scoring command was not found in `F10/G4_SCORES.md`. [open: `results/freeze10_s193/g4_score.sh` exists (S217 ls) but was not read to confirm it is the S193 scoring command]
- Hole-rate numbers for the G2 and G4 flights are not tabulated here beyond the re-fly cell. [open: not tabulated]
- G3 and G6 numbers are copied from `GATES.md` verdict sections and `GS`; the per-run files for the S199 campaign (`results/g3_campaign_f10/SCORES.tsv`) and the candidate (i) and (ii) SCORES files were not opened. [open: not compared]
- The G3 cause (actuator-model mismatch) is a hypothesis; no evidence file shows it. [open: unverified hypothesis]
- G3 PID values for draws 0 and 2 (0.768, 0.862 m) come from `GATES.md` and `REF_S241.md`; draw 0 was not re-read. [open]
- No `bench/gate_g6.sh` exists; the G6 start-error identification runs (10 starts, G2/G3/G5 per start) were not flown, so G6 items other than item 7 and the ACT_TC grid have no result here. [open: not flown]
- G6 item 2 limited to the identification-manoeuvre window was not scored separately. [open]
- G6 outlook flights on other airframes (x500, > 5 kg): no evidence found, not reported. [open]
