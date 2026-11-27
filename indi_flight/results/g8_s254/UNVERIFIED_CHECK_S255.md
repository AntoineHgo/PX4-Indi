# G8 check S255: first 10 UNCHECKED items of UNVERIFIED_CHECK.md (S254)

Method: read-only. Source files opened with grep/sed on targeted lines. Line refs below are the actual report lines; the S254 table cites some report lines off by one (noted in the table).

| item id / claim (short) | verdict | source path:line | note |
|---|---|---|---|
| 01:317-318 margin numbers come from g2_margins.md and GATES.md | STILL UNCHECKED | report/01_inner_loop_design.md:317-318 (text) | provenance statement; no per-number source map exists to compare against |
| 01:329 control allocator saturation not read | STILL UNCHECKED | none | scope note; grep "allocator"/"saturat" in GATES.md and results/*/README.md finds no allocator analysis (GATES.md:207 is G3 thrust-corner design only) |
| 01:330 cause of lower freeze-10 spot PM not established | STILL UNCHECKED | GATES.md:677-678 (spot PM 46.9 rate, 48.0 att) | numbers match the check's G2 values; the absence-of-cause claim cannot be checked by search |
| 02:347 r400/r800 suffix = --rate-hz, g2o_fly.sh:14 | VERIFIED | results/freeze9_s183/g2o_fly.sh:6,14; results/freeze9_s183/queue.sh:38-39 | queue loops r in 800 400, passed as $3 (RATE) to --rate-hz. Report text "not traced" is stale; "bench rate" wording not checked |
| 02:348 (report 349) stock MPC_* are yaml defaults, not a flight dump | VERIFIED | src/modules/mc_pos_control/multicopter_position_control_limits_params.yaml:27 (MPC_Z_VEL_MAX_UP 3.0), :91 (MPC_THR_MAX 1.0), :55 (TILTMAX_AIR 45.0), :12 (XY_VEL_MAX 12.0) | report line 349 says "not confirmed" for MPC_Z_VEL_MAX_UP/DN and MPC_THR_MAX; yaml gives 3.0 and 1.0, so that wording is stale |
| 02:350 (report 350-351) mode table in design/outer_loop_requirements.md sec 5 flags UNVERIFIED | VERIFIED | design/outer_loop_requirements.md:170 (section 5 header), :177, :179, :183 (UNVERIFIED tags) | file exists in design/, not report/ |
| 02:351 (report 352) MC_INDI_W_MAX in freeze file is line 6 | VERIFIED | results/g5_freeze_s157/params.params:6 "MC_INDI_W_MAX 2700"; ROMFS/px4fmu_common/init.d-posix/airframes/4040_gz_quad5in:54 "set-default MC_INDI_W_MAX 2700" | caveat: "freeze file" is not named in the report; g5_freeze_s157 is the S173 base per results/g3_box_s187/README.md:54. bench/params/quad5in_indi_defaults.params:5 has it on line 5 |
| 02:353 (report 354) line numbers refer to HEAD; D-OFFB-POSVEL M:599-601 now M:617-621 | STILL UNCHECKED | DECISIONS.md:977 (D-OFFB-POSVEL heading) | needs git to check HEAD line numbers (not run). Also report/02:98 says M:617-622, while report/02:354 says M:617-621 (internal inconsistency) |
| 02:354 (report 355) unit tests not read | STILL UNCHECKED | report/02:355 (text) | scope statement about what was read; cannot be verified from result files |
| 03:166, 03:343-350 G3 cause (actuator-model mismatch) is a hypothesis, no evidence file | STILL UNCHECKED | report/03_validation.md:166, :350; GATES.md:902 (same UNVERIFIED tag) | hypothesis tag is consistent across files; "no evidence file" is an absence claim not provable by search. "x2.4-2.8" tau ratio traces only to GATES.md:891 and design/route_check_241.md:9 (no motor measurement file found) |

Extra check, GATES.md:321 cites bench/gate_g3.sh: DOES NOT EXIST (ls bench/gate_g3.sh: no such file). Scripts with g3 in name in bench/: g3_score.sh, g3_score_docker.sh, g3_checks.py, g3_checks_key2.py (scoring/check by name only, not opened), plus run/sampling/analysis helpers g3_chain.sh, g3_run.py, g3_run_status.py, g3_sample.py, g3_box_margins.py, g3_osc_margins.py, g3_osc_sweep.py, g3_item2_split.py, g3_line_trace_s191.py, g3_win_detail_s191.py (GATES.md:321 wording needs a fix to bench/g3_score.sh or similar).

Counts (first 10): VERIFIED 4 (02:347, 02:348, 02:350, 02:351), WRONG 0, STILL UNCHECKED 6 (01:317, 01:329, 01:330, 02:353, 02:354, 03:166/343-350).
Flags: (a) S254 table line refs for 02:347-354 are off by one versus the report text; (b) report 02:349 "not confirmed" for MPC values is stale; (c) "freeze file" identity is inferred, not stated in the report; (d) gate_g3.sh scoring-script identities are from names only.
