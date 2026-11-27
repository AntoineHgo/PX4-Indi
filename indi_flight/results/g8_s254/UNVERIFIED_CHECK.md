# G8 check: "Unverified" claims in report chapters (S254)

Scope: report/01, 02, 03, 04, 06, A_history_errata, g2_margins ("Unverified" sections and inline tags).
Not checked as claims: report/UNVERIFIED_S217.md (38 lines, a review table, not itemised here) and
report/DOCS_DRAFT_S201.md (45 lines, not itemised here). No report file edited.

| chapter:line | claim (short) | status | evidence path:line and value found |
|---|---|---|---|
| 01:317-318 | margin numbers come from g2_margins.md and GATES.md, not result folders | UNCHECKED | meta statement about sourcing, not testable from evidence |
| 01:319-320 | G3 C3 corner from S213 verdict; "mass 1.3" has no unit | VERIFIED | GATES.md:813 "mass 1.3" with no unit (halt 2, run 024, draw 264) |
| 01:319-320 | tag "waits Q31 (G3 verdict)" | WRONG | Q31 answered at S218: GATES.md:833 "Owner amendment S218 (2026-11-23): Q31 route ... (owner answer B)". G3 final NOT PASSED: GATE_STATUS.tsv:4 (S243) |
| 01:321-322 | J_r = 5e-6 assumed; IV fit G1_Y 163-166 vs derived 205 | VERIFIED | bench/params/quad5in_indi_g1.params:12 "J_r 5e-6 ASSUMED"; design/a43_closing_s126.md:3 "IV fit 163-166"; design/key_k127_defaults.md:11 "IV fit 163-166 (-20 %), unresolved" |
| 01:323-326 | MC_INDI_ACT_TC = 0.033 equals quad5in tau; grid returns tau_sym within 0.4 % | VERIFIED | bench/params/quad5in_indi_defaults.params:21 "MC_INDI_ACT_TC 0.033"; results/actc_grid_s209/README.md symmetric rows r_slow and r_mean 0.996 / 1.002 / 1.002 (within 0.4 %) |
| 01:325-326 | params comment (Q:20) still reads UNVERIFIED | VERIFIED | bench/params/quad5in_indi_defaults.params:20 contains "UNVERIFIED mapping tau->ACT_TC" |
| 01:327-328 | MC_INDI_DELAY = 0 from filter config; other IMU_* cutoffs UNVERIFIED | VERIFIED | bench/params/quad5in_indi_defaults.params:24-25 "computed from filter config ... UNVERIFIED for non-bench filters", "MC_INDI_DELAY 0" |
| 01:329 | control allocator saturation not read (stock allocator) | UNCHECKED | scope note; no evidence file named |
| 01:330 | cause of lower freeze-10 spot PM not established | UNCHECKED | numbers agree: GATE_STATUS.tsv G2 "spot rate 46.9 / att 48.0"; GATES.md:600 freeze-7 47.8, freeze-6 54.3; cause not in evidence |
| 02:347 | cell suffix r400/r800 meaning, script g2o_fly.sh:14 | UNCHECKED | results/freeze9_s183/g2o_fly.sh:14 uses "--rate-hz $RATE"; RATE set elsewhere, not traced |
| 02:348 | stock MPC_* values are yaml defaults, not a flight dump | UNCHECKED | would need reading the yaml and flight logs (more than 2 reads) |
| 02:350 | mode table in design/outer_loop_requirements.md section 5 flags UNVERIFIED items | UNCHECKED | file not read |
| 02:351 | MC_INDI_W_MAX 2700 in airframe 4040_gz_quad5in | VERIFIED | ROMFS/px4fmu_common/init.d-posix/airframes/4040_gz_quad5in:54 "param set-default MC_INDI_W_MAX 2700" |
| 02:351 | MC_INDI_W_MAX in freeze file is its line 6 | UNCHECKED | freeze file not identified in the evidence set |
| 02:352 | 5.7 deg from asin(0.1) | VERIFIED | arithmetic: asin(0.1) = 5.739 deg (python3 check) |
| 02:353 | line numbers refer to HEAD; D-OFFB-POSVEL cites M:599-601 (now M:617-621) | UNCHECKED | line-number check needs git (not run) |
| 02:354 | unit tests not read | UNCHECKED | scope note |
| 03:166, 03:343-350 | G3 cause (actuator-model mismatch) is a hypothesis, no evidence file | UNCHECKED | absence of evidence not provable by search; not found in GATES.md G3 verdicts by keyword |
| 03:343-350 | g2_margins.md cited for method only; margin tables not compared | UNCHECKED | meta statement |
| 03:343-350 | G5 rows G5.1-G5.7 from S197 audit; S198 verdict says unchanged | UNCHECKED | GATE_STATUS.tsv:6 says "S198: audit gaps closed"; "unchanged" wording not found; needs 2+ reads |
| 03:343-350 | G1.1 and G4 reproduce commands from bench/gate_g1.sh and gate_g4.sh | VERIFIED | bench/gate_g1.sh and bench/gate_g4.sh exist (bench listing) |
| 03:343-350 | S193 G4 scoring command is results/freeze10_s193/g4_score.sh | VERIFIED | results/freeze10_s193/g4_score.sh:2 header "FREEZE-10 G4 scoring", run via run.sh with this script |
| 03:343-350 | hole-rate numbers not tabulated | UNCHECKED | meta statement |
| 03:343-350 | per-run SCORES files of S199 campaign and candidates not opened | UNCHECKED | meta statement |
| 03:343-350 | G3 PID draw 0 0.768 m, draw 2 0.862 m | VERIFIED | GATES.md:905 "draw 0 (0.418 vs 0.768 m)"; GATES.md:893 and results/g3_routeB_s239/REF_S241.md:16 "PID 0.862" |
| 03:343-350 | no bench/gate_g6.sh exists | VERIFIED | bench/ contains gate_g1.sh, gate_g4.sh, gate_g8.sh, pretest_gate.py only |
| 03:343-350 | G6 runs not flown | UNCHECKED | would need G6 results folder search |
| 04:94-99 (inline 21) | 2 Hz pitch mode INDI-specific rests on one PID flight per draw and seed | VERIFIED | results/g3_routeB_s239/REF_S241.md:36-38 (one PID draw 3 run, one INDI re-fly); no spread given |
| 04:94-99 | actuator-model mismatch hypothesis | UNCHECKED | same as 03 hypothesis row |
| 04:94-99 | "6 LOC in 58" with four watchdog stops counted as LOC | VERIFIED | GATES.md:922-924 "Item 1 FAILS ... 262, 264, 269 and 292 were stopped by the flight watchdog ... 6 LOC in 58 runs" |
| 04:94-99 | 4.3 anomaly list one-line summaries from ANOMALIES.md | UNCHECKED | list not re-read |
| 04:94-99 | motor tau and telemetry latency in ch. 6 map to 4.1 region | UNCHECKED | judgement; ch. 6 body not read |
| 06:68 | A-57 frozen detector trip at 0.075 s with 0.5 s window, cause unverified | VERIFIED | ANOMALIES.md:34 "trip at +0.075 s after SIM_GZ_ERPM_FRZ set ... MC_INDI_ERPM_FRZ is 0.5 s ... unverified" |
| 06:118-135 | B3 telemetry rate, B4 latency (g2_margins.md:9-10 "not found"), B8 loop rate and CPU | UNCHECKED | needs flight or hardware; no evidence file |
| 06:118-135 | B5 esc_rpm tolerance vs tachometer; real trip time (A-57 open) | UNCHECKED | needs tachometer test; A-57 part checked above |
| 06:118-135 | B6 real DShot driver loss behaviour | UNCHECKED | needs hardware |
| 06:118-135 | second esc_status instance on a real board | UNCHECKED | needs real board |
| 06:118-135 | guard params ERPM_TO, ERPM_FRZ, SP_TO, INC_MAX tuned for hardware | UNCHECKED | needs hardware flight |
| 06:118-135 | yaml:126-128 unchanged at S217; ident_actc.py on hardware needs a flight | UNCHECKED | yaml now at src/modules/mc_indi_rate_control/mc_indi_rate_control_params.yaml:126-128 (min 0.001, max 0.2, unit s); "unchanged at S217" is history, needs git |
| 06:118-135 | default values read from yaml; line numbers not cited | UNCHECKED | meta statement |
| 06:118-135 | (closed S217) DSHOT_MOT_POL default 14 at src/drivers/dshot/module.yaml:87 | VERIFIED | src/drivers/dshot/module.yaml:87 "default: 14" |
| A:168-185 | exact first sessions of stages 5, 6, 7 not found by keyword | UNCHECKED | needs journal read |
| A:168-185 | LESSONS.md lesson 1 labels 5 Hz metric "Stage 1" | VERIFIED | indi_flight/LESSONS.md:10 "Stage 1: bench/metrics.py scored trajectories ... at 5 Hz" (conflict with archive review itself not resolved here) |
| A:168-185 | archive results re-scored with corrected metric not checked | UNCHECKED | meta statement |
| A:168-185 | G1 first-test session S19-S24 from JOURNAL 73-75 and Q2 | VERIFIED | indi_flight/JOURNAL.md:73-75 entries for S19 (launch 20261115), S22, S24 |
| A:168-185 | Q31 outcome not known and not stated | WRONG | answered at S218: GATES.md:833 "Owner amendment S218 (2026-11-23): Q31 route and gate binary (owner answer B, D-OWNER-Q31)" |
| g2_margins:155 | effective MPC_* values in flown runs unverified in source | UNCHECKED | needs flight logs search |
| g2_margins:155 | attitude latency (1 sample) and yaw not modelled | UNCHECKED | model code not read |
| g2_margins:153-155 | GM bounds measured >= 21.8 dB and model >= 17.2 dB | UNCHECKED | literal values not in g2_margins.md or ANOMALIES.md; A-36 (ANOMALIES.md:27) gives model 1.6-4.6 dB below measured, which is consistent with 21.8 - 4.6 = 17.2 for the worst case |

## Counts

- VERIFIED: 17
- WRONG: 2
- UNCHECKED: 30
- Total items: 49

WRONG items:
- 01:319-320 tag "waits Q31": Q31 answered B at S218 (GATES.md:833); G3 final NOT PASSED (GATE_STATUS.tsv:4).
- A chapter, Q31 item: Q31 answered B at S218 (GATES.md:833), not "not known".

Notes:
- bench/gate_g3.sh is cited in GATES.md:321 but is not present in bench/ (only gate_g1.sh, gate_g4.sh, gate_g8.sh, pretest_gate.py match "gate").
- LESSONS.md:10 vs the archive review on the Stage 1 label remains a conflict (not resolved here).
