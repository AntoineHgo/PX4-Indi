# G3 pre-test (S173): first 20 draws of the G3 campaign (master seed 173, n 300)

Firmware aa4fd2654a (D-JFF-OFFB), base params `results/g5_freeze_s157/params.params`, serial, one container per run.
Fly: `bash indi_flight/results/g3_pretest_s173/fly.sh 0 19` (skips done runs); progress in progress.txt.

Status S173: flown only. 20/20 docker rc 0 and run.json exit_status ok. Scenarios: o1_lemniscate 17, stick_zsine_o6 3
(check this mix against the MODE_MIX of bench/g3_sample.py before the campaign). Each run dir holds g3_draw.json
(plant draw), g3_params.txt, g3_scenario_overrides.json, disturbance_summary.json.

Not yet done (S174): score with bench/g3_checks.py (needs per-scenario --t0/--t1 windows, gate_g3.sh still deferred),
check every factor applied (run_validity.py, g3_done.json applied/not_applied), explain every failure before counting.
