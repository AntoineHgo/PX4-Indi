# Agent ledger (not read at launch)

One row per agent, newest first: append when an agent ends. Read it only to size a new brief.
Stage-1 rows are in JOURNAL.md. Moved out of STATE.md on 2026-11-17 (token economy, owner).

| session | id | model | task | outcome |
|---|---|---|---|---|
| 65 | T132 | sonnet | N1 C2 disturbance sizing + self-test | done, 9 calls, ~$0.3, test OK, UNKEYED, guard blocked 1 call (cause unknown) |
| 65 | T131 | haiku | G3 hooks existence check | done, 5 calls, ~$0.06 |
| 64 | T130 | sonnet | draft G3-G8 tests | done, 4 calls, ~$0.35, 154 lines, one wrong T/W (53, real 7.3) caught in review |
| 64 | T129 | sonnet | route check 64 | done, 4 calls, ~$0.15, acted on |
| 63 | T128 | sonnet | primary G2-STEP metric script + 7 self-tests | done, 8 calls, ~$0.4, break-checked, AGREE with T127 key 9/9 |
| 62 | T127 | haiku | second key step metrics (independent script) | done, 8 calls, ~$0.08, AGREE 27/27; truth offsets -> A-28 |
| 62 | T126 | haiku | second key da64bc26b3 vs D-S3-ATT-STEP | done, 3 calls, ~$0.06, AGREE-WITH-ISSUES, yaw toggle fixed |
| 62 | T125 | sonnet | code D-S3-ATT-STEP + tests + builds | done, 15 calls, ~$0.5, model test OS 0.51 % (11.1 % without), break-checked, committed da64bc26b3 |
| 61 | T124 | haiku | second key attitude-step model | done, 6 calls, ~$0.07, AGREE (settle differs at band edge) |
| 60 | T123 | haiku | second key slice INDI stage vs A2-A14 | done, 8 calls, ~$0.06, AGREE with 3 deviations |
| 60 | T122 | sonnet | stage-5 hover slice code+build+1 hover | done, 28 calls, ~$0.8, flew; claimed module identity unverified, closed by S60 instrument |
| 59 | T121 | sonnet | route check 59 | done, 4 calls, ~$0.15, acted on |
| 59 | T120 | haiku | second key items 2+3 diff | done, 5 calls, ~$0.06, AGREE-WITH-ISSUES (5 minor) |
| 59 | T119 | sonnet | code items 2+3 + tests | done, 7 calls, ~$0.33, 6/6 pass, break-checked |
| 58 | T118 | haiku | second key items 1+4 diff | done, 6 calls, ~$0.06, AGREE-WITH-ISSUES (issue unreachable) |
| 58 | T117 | sonnet | code items 1+4 + tests | done, 27 calls, ~$0.7, all pass, break-checked, module not compiled by it |
| 57 | T116 | sonnet | G2 outer break note | done, 8 calls, ~$0.7, 59 lines, UNKEYED |
| 57 | T115 | sonnet | route check 57 | done, 6 calls, ~$0.18, acted on |
| 56 | T114 | haiku | second key D-YAW-INV diff | done, 5 calls, ~$0.05, AGREE-WITH-ISSUES, landed-cycle bug found and fixed |
| 56 | T113 | sonnet | code D-YAW-INV + tests | done, 13 calls, ~$0.45, all pass, break-checked, missed first landed cycle |
| 54 | T111 | sonnet | second key yaw break model | done, 6 calls, ~$0.25, coded-law denominator mis-transcribed; AGREE after 1-line fix, option (c) AGREE |
| 53 | T110 | sonnet | route check 53 | done, 6 calls, ~$0.2, acted on (defaults, G2 table first) |
| 53 | T109 | sonnet | stage-3 items design note | done, 5 calls, ~$0.2, 168 lines, UNREVIEWED |
| 52 | T107 | sonnet | code MC_INDI_LEAD + tests | done, 14 calls, ~$0.75, all pass, break-checked |
| 52 | T108 | haiku | second key lead diff vs note | done, 6 calls, ~$0.08, AGREE, 1 logging finding fixed |
| 51 | T106 | haiku | A-24 PSD re-check with G2_Y 27 | done, 5 calls, ~$0.1, tone gone ~100x |
| 51 | T105 | opus | review r1 lead note vs code | done, 9 calls, ~$1.1 (2x estimate), NOT BLOCKING, 3 MAJOR |
| 66 | T133 | haiku | second key T132 disturbance sizing | done, 12 calls, AGREE, note errata |
| 66 | T134 | haiku | G1.5 pre-test 5 profiles quad5in | done, 16 calls, 5/5 flew, 3 response findings |
| 66 | T135 | sonnet | N2-A anomaly triage pre-S36 | done, 11 calls, verdicts applied (A-7 parked not closed) |
| 66 | T136 | sonnet | investigate payload/com_shift/torque sign | done, 15 calls, wrench 2x found (A-31) |
| 66 | T137 | sonnet | A-31 gz ApplyLinkWrench source read | done, 11 calls, no 2x mechanism in source |
| 67 | T138 | sonnet | A-31 fix + solo re-fly payload_add, com_shift | done, 10 calls, 1x confirmed |
| 67 | T139 | haiku | second key T138 from raw logs | done, 9 calls, AGREE |
| 67 | T140 | haiku | re-fly torque_steps, gust_x, gust_diag after fix | done, 8 calls, main axes halved |
| 67 | T141 | haiku | A-30 re-fly 400 Hz A/B/C | done, 10 calls, DIFFERENT -> Q5 |
| 67 | T142 | sonnet | A-9 on new module (read) | done, 8 calls, NO PATH, test design only |
| 67 | T143 | haiku | INDI same-seed batch 400 Hz 8 runs | done, 10 calls, spread measured, S64 seed1 outlier |
| 67 | T144 | haiku | S64 outlier log diff | done, 8 calls, params same, S64 dirty build |
| 68 | T145 | haiku | clean-HEAD re-fly G2-STEP 400 + 800 Hz same-seed | done, 22 calls, 14/14 pass |
| 68 | T146 | sonnet | A-9 second key + guard gtest | done, 11 calls, AGREE, test added |
| 68 | T147 | haiku | same-seed spread with --sched | done, 20 calls, rise spread 6/15 ms remains |
| 68 | T148 | haiku | A-30 discriminator PID / v2true / eRPM lost | done, 14 calls, all spread: not INDI |
| 68 | T149 | haiku | sim v1 vs v2 determinism (G1.6 cmd) | done, 8 calls, both spread ~11 ms |
| 68 | T150 | haiku | re-score G1.6 runs with both metrics | done, 8 calls, real regression -> A-32 |
| 69 | T152 | sonnet | route check 69 | done, 5 calls |
| 69 | T154 | sonnet | slice-2 build plan (read-only) | done, 10 calls |
| 69 | T155 | haiku | slice-2 plan fact check | done, 5 calls |
| S70 | T156 | sonnet | slice-2 part 1: gap scenarios, checker+test, 7 flights | 29 calls, ~71k tok, ~$0.55 | done, results/stage5_s70 |
| S70 | T157 | haiku | blind second key on gap z-error | 11 calls, ~39k tok | done, agrees <= 0.006 m |
| S71 | T158 | opus | D-GAP review r1 | 15 calls, ~62k tok, ~$0.7 | done, BLOCKING (edge semantics), design/dgap_review_r1.md |
| S71 | T159 | sonnet | D-GAP r2 closure check | 3 calls, ~29k tok, ~$0.13 | done, OPEN on wording -> fixed, design/dgap_review_r2.md |
| S72 | T160 | sonnet | D-GAP impl + 8 tests + 2 flights | 36 calls, ~90k tok, ~$0.8 | done; orchestrator fixed reset() model-path init (+1 test, break-checked) |
| S72 | T161 | haiku | second key dz + residual split | 8 calls, ~41k tok, ~$0.1 | done, results/stage5_s72/second_key.md |
| S72 | T162 | haiku | A-33 split on 3 logs | 6 calls, ~39k tok, ~$0.07 | done, results/stage5_s72/a33_split.md |
| S74 | T163 | sonnet | route check 74 | 6 calls, ~36k tok, ~$0.19 | done, design/route_check_74.md |
| S74 | T164 | haiku | rate-blend edge survey | 10 calls, ~41k tok, ~$0.04 | done, design/rate_blend_survey_s74.md |
| T164 | S77 | sonnet | D-RATE-BLD unit tests (edges + weak-motor closed loop) | results/stage3_s77_tests/README.md | running |
| T164 | S77 | sonnet | done: 3 blend tests, 69/69, break-checked, 13 calls | results/stage3_s77_tests/README.md |
| T165 | S77 | haiku | velocity-break injector search: none exists, 11 calls | results/stage3_s77_400/velbreak_search.md |
| T166 | S78 | sonnet | A-34 setpoint lead in margins_models.py, shift reproduced, bins fail (A-35), 18 calls, ~$0.44 | results/stage3_s78_a34/README.md |
| T167 | S78 | sonnet | second key of the lead model: no BLOCKING, 2 MINOR (test Tc fixed), 4 calls, ~$0.15 | results/stage3_s78_a34/second_key.md |
| 79 | T168 | sonnet | route check 79 | done, 5 calls, ~$0.2, acted on (default committed, A-34/A-35 parked) |
| T170 | S82 | sonnet | outer-loop break injector (38 tool calls, ~97k tokens, ~$0.4) | results/stage5_s82_velbreak/NOTES.md | done, committed |
| T171 | S83 | sonnet | injector second key, AGREE WITH MINOR, 13 calls | results/stage5_s82_velbreak/second_key.md |
| T172 | S83 | haiku | stick stub second key, DISAGREE (valid), 13 calls | results/stage5_s81_stick/second_key.md |
| T173 | S83 | sonnet | injector minors + pinj_csv self-test, 24 calls, ~$0.25 | results/stage5_s83_velbreak/minors_fix.md |
| T174 | S84 | sonnet | accel-loop stage-output break, 20 calls, ~$0.4 | results/stage5_s84_accbreak/NOTES.md | done, committed |
| RC84 | S84 | sonnet | route check 84, 8 calls, ~$0.5 | design/route_check_84.md | done, acted on |
| T175 | S84 | sonnet | second key of T174, 10 calls, ~$0.15 | results/stage5_s84_accbreak/second_key.md | AGREE WITH MINOR, minors fixed or accepted |
| T176 | S85 | sonnet | HF FRF second key + pinj_csv fix, 11 calls, ~$0.2 | results/stage5_s84_accbreak/hf_second_key.md | AGREE; found margins_est DC defect |
| T177 | S85 | sonnet | per-run hole reporter + self-test, 10 calls, ~$0.2 | results/stage5_s85_holes/README.md | done, committed |
| T178 | S85 | sonnet | second key of hole_report, 8 calls, ~$0.15 | results/stage5_s85_holes/second_key.md | AGREE WITH MINOR, fixes queued S86 |
| T179 | S86 | sonnet | hole_report fixes + break tests, 11 calls, ~$0.15 | results/stage5_s85_holes/fixes_s86.md | done 98e977a9f0 |
| T180 | S86 | sonnet | attitude-break design note, 18 calls, ~$0.3 | design/attitude_break_s86.md | done, unreviewed |
| T181 | S86 | sonnet | xy break diagnosis from logs, 13 calls, ~$0.15 | results/stage5_s86_g2outer/t181_xy_diagnosis.md | done, top_db misread |
| T182 | S87 | sonnet | hole_report count fix + re-run | ~32 calls | DONE |
| T183 | S87 | haiku | second key T181 xy FRF | 9 calls | DONE AGREE |
| T184 | S87 | haiku | second key T182 | 14 calls | DONE AGREE WITH MINOR |
| T185 | S87 | sonnet | review attitude-break note vs code | 10 calls | DONE 0 blocking |
| T186 | S88 | sonnet | hole_report fixes | done |
| T187 | S88 | haiku | top_db rename (README rewrite reverted) | done |
| T188 | S88 | haiku | second key T186 | done, AGREE WITH MINOR |
| T189 | S89 | haiku | hole_report re-run 26 cells | rerun_s89.md | done |
| RC89 | S89 | sonnet | route check 89 | design/route_check_89.md | done |
| T190 | S90 | sonnet | amend attitude-break note + implement injector, call-site test, check script | design/t190_impl_log.md | done (25 calls) |
| T191 | S90 | sonnet | second key b41dd6ec81 vs attitude-break note sec 1-3,8 | design/attitude_break_s90_key.md | done (14 calls), 0 BLOCKING 3 MAJOR |
| T192 | S91 | sonnet | ratesp_csv.py extractor + self-test | DONE |
| T193 | S91 | sonnet | second key of ratesp_csv.py | AGREE WITH MINOR |
| T194 | S93 | sonnet | attitude-break linear model + tests + table | 16 calls, ~$0.45 | DONE |
| T195 | S93 | sonnet | key: outer-loop factor from firmware | 9 calls, ~$0.25 | DONE agrees |
| RC93 | S93 | sonnet | route check 93 | 6 calls, ~$0.15 | DONE |
| T196 | S94 | sonnet | G2 report section draft | 18 calls, ~$0.45 | DONE, 2 numbers spot-checked |
| T197 | S94 | sonnet | G3-G8 final text proposal + hook table | 15 calls, ~$0.45 | DONE, 8 decisions applied |
| T198 | S94 | sonnet | delay-line hook design note | 10 calls, ~$0.25 | DONE, step size and GNSS path unverified |
| S95 | T198 | opus | stage-3 safety review | 13 calls, ~68k tok, ~$0.65 | NOT BLOCKING, 1 MAJOR |
| S95 | T199 | opus | stage-5 D-GAP slice review | 11 calls, ~77k tok, ~$0.7 | BLOCKING (disputed), 4 MAJOR |
| S96 | T200 | sonnet | D-GAP fixes F1-F5 + tests | 28 calls, ~87k tok, ~$0.5 | DONE bf44ece093 |
| S96 | T201 | sonnet | autotune start + watchdog receipt time | 5 calls, ~$0.1 | DONE b7a171b4b5 4385e8f56a |
| S96 | T202 | sonnet | second key on bf44ece093 | 8 calls, ~55k tok, ~$0.2 | DONE, 2 MAJOR (one vacuous test the author had reported as break-checked) |
| S96 | T203 | haiku | key on dff2b7a805 | 7 calls, ~$0.03 | DONE OK, 1 MINOR |
| S97 | T204 | sonnet | D-ALTCTL-Z implementation + 6 tests | 16 calls, ~60k tok, ~$0.25 | DONE 52beee60e5, 1d827d62be |
| S97 | T205 | sonnet | second key on 52beee60e5, de7c598e1e | 16 calls, ~69k tok, ~$0.3 | DONE no BLOCKING, 2 MAJOR coverage, MINORs |
| S98 | RC98 | sonnet | route check 98 | 10 calls, ~39k tok, ~$0.1 | DONE (one wrong claim: G3-G8 text already in GATES.md) |
| S98 | T206 | sonnet | lib mutation tests + module gate | 18 calls, ~63k tok, ~$0.35 | DONE b6e95f88c4 c32d022f9e |
| S98 | P98 | sonnet | G5 gap pre-test 3 flights | 17 calls, ~46k tok, ~$0.3 | DONE a462b69ad5 |
| S98 | K98 | haiku | second key P98 from raw ulg | 9 calls, ~37k tok, ~$0.03 | DONE agrees |
| S100 | K100 | sonnet | second key G2 rate cells 12 flights | 5 calls, ~35k tok | DONE 9621a25d3d 12/12 agree |
| S100 | P100 | haiku | model-only rate pre-test 2 flights | 15 calls, ~47k tok | DONE db536a8c01 PASS |
| S100 | B100 | haiku | model-only rate batch 10 flights | - | in flight |
| K101 | S101 | self (docker, no agent) | second key of 12 model-only G2 rate cells | results/g2_rate_modelonly_s100/key_k101/summary.md | DONE 12/12 agree |
| S102 | H102 | sonnet | delay-line hooks A1+A2 gz_bridge, build | 21 calls, ~60k tok | DONE builds, uncommitted |
| S102 | K102 | sonnet | second key H102 code vs spec | 12 calls, ~47k tok | DONE 0 BLOCKING, 2 MAJOR fixed |
| S102 | V102 | haiku | delay-hook pre-test 2 flights | 13 calls, ~40k tok | DONE IMU PASS, ACT unverified (A-37) |
| S103 | RC103 | sonnet | route check | 7 calls, ~37k tok | DONE design/route_check_103.md |
| S103 | S103 | haiku | POSCTL gap scenario scope | 6 calls, ~31k tok | DONE design/posctl_gap_scope_s103.md |
| G104 | S104 | haiku | G2 verdict note scope (read-only) | 13 calls, ~53k tok, ~$0.06 | DONE design/g2_verdict_scope_s104.md |
| X105 | S105 | sonnet | G2 model-vs-measured cross-check (offline) | 14 calls, ~55k tok, ~$0.35 | DONE design/g2_crosscheck_s105.md |
| H106 | S106 | sonnet | hook B GNSS delay impl+build+1 flight | 14 calls, ~46k tok, ~$0.3 | DONE design/gnss_delay_impl_s106.md, d52576b02a |
| K106 | S106 | sonnet | second key hook B + 2 flights L=250 | 11 calls, ~43k tok, ~$0.3 | DONE: 1 BLOCKING (SENS_GNSS0_DELAY inert), fixed 99673b62bd |
| K107 | S106 | sonnet | second key of fix 99673b62bd (read-only) | 3 calls, ~29k tok, ~$0.1 | DONE: no BLOCKING, 1 MINOR accepted |
| B107 | S107 | sonnet | attitude-break G2 cells at HEAD (6 flights) | 13 calls, ~35k tok, ~$0.5 | DONE 8ec7d4a95b: 6/6 PASS |
| Y107b | S107 | sonnet | yaw model second key + 8-cell cross-check (offline) | 32 calls, ~75k tok, ~$0.6 | DONE design/g2_yaw_crosscheck_s107.md, A-39 |
| RC108 | S107 | sonnet | route check (filed early) | 5 calls, ~33k tok, ~$0.15 | DONE design/route_check_108.md, accepted with amendment (G3/G5 before freeze = probes) |
| D107 | S107 | sonnet | draft G2 verdict update (no edits to GATES.md) | 7 calls, ~37k tok, ~$0.15 | DONE design/g2_verdict_s108_draft.md |
| D107-review | S108 | self | review of D107 draft against result READMEs | ~8 calls | DONE: outer-cell omission corrected, 93f94320d3 |
| G108 | S108 | sonnet | G3 sampler + self-test + hook map | 19 calls, ~85k tok, ~$0.65 | DONE 238079b24f |
| K108 | S108 | sonnet | second key of g3_sample.py | 11 calls, ~71k tok, ~$0.45 | DONE 0 BLOCKING 4 MAJOR 8 MINOR |
| F109 | S109 | sonnet | G3 sampler fix per D-G3-SAMPLER-K108 | 8 calls, ~55k tok, ~$0.35 | DONE 3a245d1590, 16 mutations caught |
| K109a | S109 | sonnet | second key of F109 (read-only) | 5 calls, ~32k tok, ~$0.15 | DONE 0 BLOCKING 0 MAJOR 2 MINOR (closed e634a78671) |
| V109 | S109 | sonnet | quad5in plant variants + mass flight check | 13 calls, ~41k tok, ~$0.45 | DONE bd612779a1, 45f2b6d2c9 |
| K109 | S109 | sonnet | second key of V109 (read-only, offline SDF diff) | 6 calls, ~33k tok, ~$0.2 | DONE 0 BLOCKING 1 MAJOR (driver, S110) 2 MINOR |
| R110 | S110 | sonnet | G3 driver g3_run.py + self-test, dry-run only | 16 calls, ~56k tok, ~$0.35 | DONE c5acce1b39; K109 MAJOR closed; 6 factors unmapped |
| O110 | S110 | sonnet | scenario overrides + wind params + g3_run mapping + 1 flight | 33 calls, ~85k tok, ~$0.55 | DONE fc3ef9e626, 48ef5120e5 |
| K110 | S110 | sonnet | second key of O110 (read-only, mutations in temp copies) | 23 calls, ~61k tok, ~$0.3 | DONE 0 BLOCKING 3 MAJOR 3 test gaps |
| F111 | S111 | sonnet | fix K110 M-1..M-3, m-2, m-6, 3 mutations | 31 calls, ~79k tok, ~$0.65 | DONE b0486b703e |
| K111 | S111 | sonnet | second key of b0486b703e (read-only, mutations) | 21 calls, ~55k tok, ~$0.37 | DONE 0 BLOCKING 2 MAJOR |
| G111 | S111 | sonnet | close K111 F-1/F-3/F-5, test exit codes | 20 calls, ~54k tok, ~$0.4 | DONE 6e8c4fa474 |
| P112 | S112 | sonnet | 3-flight G3 hook pre-test | 76 calls, ~109k tok, ~$1.2 | DONE 4 set-up faults (README) |
| RC113 | S113 | sonnet | route check 113 | 8 calls, ~34k tok, ~$0.15 | DONE design/route_check_113.md |
| F113 | S113 | sonnet | fix P112 faults 1, 2, 4b | 36 calls, ~78k tok, ~$0.45 | DONE 09515cd8ae |
| K113 | S113 | sonnet | key of 09515cd8ae | 12 calls, ~39k tok, ~$0.2 | DONE 0 BLOCKING 0 MAJOR 3 MINOR |
| M113 | S113 | sonnet | stick_zsine_o6 mass-only discriminator, 3 flights | 18 calls, ~51k tok, ~$0.3 | DONE set-up fault (stabilized hover stick) |
| K114 | sonnet | key of stick fix 807fd6a08a | design/key_k114_stick.md |
| F114 | haiku | re-fly stick_zsine_o6 stabilized INDI+PID | results/g3_stick_s114/README.md |
| S115 | A40 | haiku | A-40 early landing cause | results/g3_stick_s114/a40_cause.md | done, 10 calls, A-40 closed |
| S116 | K115 | sonnet | key of 8f57b47f7e (HTE valid) | design/key_k115_hte.md | done, 6 calls, 0 BLOCKING |
| S116 | L116 | haiku | single-factor ladder 9 flights | results/g3_ladder_s116/README.md | done, 33 calls (first launch wrong params path, re-run) |
| S116 | L116b | haiku | 6 control flights (PID stick, INDI lemniscate) | same README sec b | done, 13 calls |
| S116 | N116 | haiku | nominal lemniscate INDI+PID | same README sec c | done, 11 calls, A-41 closed |
| S116 | H116 | sonnet | K115 fixes + tests | design/key_k115_hte.md | done, 8 calls |
| S116 | A116 | haiku | altctl/posctl stick flyability 3 flights | results/g3_stick_modes_s116/README.md | done, 9 calls (README by orchestrator) |
| S117 | G117 | sonnet | sampler stick-factor rule + 4 tests + DECISIONS | bench/g3_sample.py | done, 19 calls, mutations checked |
| S118 | RC118 | sonnet | route check | design/route_check_118.md | done, 6 calls |
| S118 | I118 | sonnet | stick pilot impl + tests | design/i118_stick_pilot.md | done, 10 calls |
| S118 | K118 | sonnet | key of pilot | design/key_k118_pilot.md | done, 8 calls, 0 BLOCKING 2 MAJOR |
| S118 | F118 | sonnet | pilot fixes + 3 tests | design/i118_stick_pilot.md F118 | done, 16 calls |
| S119 | I119 | sonnet | IV ident estimator + self-tests | design/i119_ident_iv.md | launched |
| S120 | K120 | sonnet | second key ident_iv.py (re-impl 2SLS, mismatch, HAC) | design/key_k120_ident_iv.md | done: 1 BLOCKING + 2 MAJOR fixed, 20/20 |
| S120 | H120 | haiku | M3a injection signals survey | design/h120_m3a_signals.md | done (rate claim unverified) |
| S122 | RC122 route check | sonnet | design/route_check_122.md | done, accepted |
| S122 | torque_measured logging cause | sonnet | design/s122_torque_measured_logging.md | done: MC_INDI_W_MAX unset |
| S122 | run_validity.py + g3_run wiring + tests | sonnet | design/s122_run_validity.md | done, 23 tests |
| S122 | K122 key of run_validity | sonnet | design/key_k122_run_validity.md | done, 3 BLOCKING open |
| S123 | fix K122 3 BLOCKING (run_validity/g3_run) | sonnet | design/fix_k122_s123.md | done, 26 tests, broken-checked, 9 calls ~$0.17 |
| S123 | M3a ident hover pretest POS_EN 0/1 | sonnet | results/ident_m3a_s123/README.md | done, both valid, 11 calls ~$0.20 |
| S124 | IV fit driver + fit pos0/pos1 | sonnet | results/ident_m3a_s123/fit_s124.md | done, G1_R 1748, 34 calls ~$0.55 |
| S124 | K124 key of ident_fit.py | sonnet | design/key_k124_ident_fit.md | done, 3 BLOCKING 6 MAJOR 4 MINOR, 14 calls ~$0.30 |
| S124 | fix K124 BLOCKING + re-fit | sonnet | design/fix_k124_s124.md | done, 10 tests, 25 calls ~$0.75 |
| S125 | K125 re-key of K124 fix | sonnet | design/key_k125_fix_k124.md | done, 13 calls ~$0.2 |
| S125 | yaw two-regressor IV fit | sonnet | results/ident_m3a_s123/fit_yaw_s125.md | done, 21 calls ~$0.45, 25 min |
| S125 | fix K125 gaps A+B | sonnet | design/fix_k125_s125.md | done, 18 calls ~$0.25 |
| S126 | A-43 source chain G1_Y from SDF/plugin/CA | sonnet | design/a43_closing_s126.md | done, 205.3, roll/pitch reproduced, 19 calls ~$0.2 |
| S126 | K126 key of ident_fit_yaw.py | sonnet | design/key_k126_ident_fit_yaw.md | done, 0 B 4 MAJ 6 MIN, 16 calls ~$0.25, 13 min (self-test 244 s) |
| S126 | A-43 probe: interp / rate regressor / synthetic | sonnet | results/ident_m3a_s123/a43_probe/README.md | done, cause = omitted D r, 9 calls ~$0.2 |
| S127 | defaults draft from derived values | sonnet | design/defaults_s127.md | done, 7 calls ~$0.17, unkeyed, 8 UNVERIFIED |
| S127 | K127 key of defaults params | sonnet | design/key_k127_defaults.md | done, 0 B 3 MAJ, 5 calls ~$0.13 |
| S128 | impl D-DEFAULTS-FW (ID_OK gate, defaults) | sonnet | design/impl_s128_id_ok.md | done, 10 calls ~$0.28, 2.3 min |
| S128 | K128 key of ID_OK diff | sonnet | design/key_k128_id_ok.md | done, 0 B 1 MAJ 3 MIN, 4 calls ~$0.1 |
| S128 | smoke hover ID_OK 0 | haiku | results/smoke_s128_idok0/README.md | done, ok after runner MC_RATE_CTL_TYPE retry, 17 calls ~$0.15 |
| S128 | ACT_TC pretest 4 flights | haiku | results/act_tc_s128/README.md | done, 11 calls ~$0.15 |
| S128 | RC129 route check | sonnet | design/route_check_129.md | done, 7 calls ~$0.15 |
| S129 | sonnet | G5 build list | design/g5_build_list.md | 22 calls, done |
| S130 | impl D-STAGE-STALE + IndiStageMode helper/gtests | sonnet | design/impl_s130_stage_stale.md | done, 14 calls ~$0.35 |
| S130 | K130 key | sonnet | design/key_k130_stage_stale.md | done, 9 calls ~$0.15 |
| S130 | smoke hover+POSCTL | haiku | results/smoke_s130_stage/README.md | done, 15 calls ~$0.1 |
| S130 | lib fix f_b_valid | sonnet | design/impl_s130b_model_fb.md | done, 12 calls ~$0.3 |
| S130 | K130b key | sonnet | design/key_k130b_model_fb.md | done, 4 calls ~$0.17 |
| S131 | impl T5 failsafe fn + T10 reset | sonnet | design/impl_s131_failsafe_reset.md | done, 20 calls ~$0.4 |
| S131 | K131 key | sonnet | design/key_k131_failsafe_reset.md | done, 9 calls ~$0.18, 0 BLOCKING/MAJOR |
| S131 | AUTO harness T2-T6 + 2 smokes | sonnet | design/impl_s131_auto_harness.md | done, 32 calls ~$0.6 |
| S131 | PID ref auto_land10 | haiku | results/auto_smoke_s131_pid/README.md | done, 9 calls ~$0.05 |
| S131 | A-45 cause search | sonnet | design/a45_cause_s131.md | done, 12 calls ~$0.22, partial (bypass path) |
| S132 | K132 key review D-HANDOVER diff | sonnet | design/review_k132_handover.md | done, 9 calls ~$0.25, 0 BLOCKING, 1 MAJOR fixed |
| S133 | B133 T9 hover-thrust port | sonnet | design/impl_s133_t9_hover_thrust.md | done, 24 calls ~$0.32, gtest break-checked |
| S133 | A133 T7/T8 smokes | sonnet | design/impl_s133_offboard_passthrough.md | done, 18 calls ~$0.38, 2 SITL flights |
