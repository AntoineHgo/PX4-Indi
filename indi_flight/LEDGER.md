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
