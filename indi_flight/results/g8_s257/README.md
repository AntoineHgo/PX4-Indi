# G8 S257 report clean-up log
Task 1: all UNCHECKED items of g8_s254/UNVERIFIED_CHECK.md (30) and UNVERIFIED_CHECK_S255.md (14 still unchecked) name
claims that already sit in the "Unverified" section of their chapter (01:317-330, 02:347-354, 03:343-350, 04:94-99,
06:118-135, A:168-185, g2_margins:155), each with an `[open: ...]` tag or the section heading. Action: left marked (no
deletion). Items 21-30 of the first file (06 B6, second esc_status, guard params, yaml 126-128, A first sessions,
re-score, g2_margins MPC_*, attitude latency, GM bounds) same: already marked. WRONG items (01:319 Q31 tag, A Q31) were
already fixed to "answered B S218, G3 NOT PASSED S243" in the text. Counts: marked 0 new (all already marked), deleted 0, fixed 0 new.
Task 2: report/02_outer_loop_design.md "not confirmed" lines replaced with the yaml defaults, source
src/modules/mc_pos_control/multicopter_position_control_limits_params.yaml (MPC_Z_VEL_MAX_UP 3.0 line 27, _DN 1.5 line 42,
MPC_THR_MAX 1.0 line 91), flight dump still absent (marked unverified). GATES.md line 321 now cites bench/g3_score.sh,
g3_checks.py, g3_checks_key2.py (all exist).
Task 3: docs/en/config_mc/indi_control.md: 4 relative links resolve, 27 reference links all defined, no code fences,
headings h1/h2/h3 ordered. npx not available, no prettier run; manual check; 3 tables re-padded (alignment only).
Task 4: gate_g8.sh 7/7 PASS (gate_g8_out.txt), including check 1.
Task 5: VERDICT_DRAFT.md.
