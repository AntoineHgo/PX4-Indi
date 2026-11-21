# FREEZE-10 gate re-fly queue (S193)

Firmware 7fe6206fcc (D-FREEZE-10, DECISIONS.md), SITL binary build/px4_sitl_default/bin/px4 built 22:38:25 after the last src commit (22:37:34). Params
results/g5_freeze_s157/params.params (MC_INDI_POS_EN 1, XY gains at firmware defaults). Tooling copied from freeze9_s183 / g3_pretest_s190 with paths rewritten (sed), no new metric code.

Launch: 2026-11-21 22:58:28 CET. `cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi && nohup setsid bash indi_flight/results/freeze10_s193/queue.sh > indi_flight/results/freeze10_s193/queue.nohup.log 2>&1 < /dev/null &`
Queue PID 1308846 (setsid, no separate waiter). Log queue.nohup.log, queue.log; per-step status queue_status.tsv (name, start, end, rc). `ABORT` row = first flight of a step left no log.
First check 22:59: container px4-indi-g3p193_0 up, run_000 files growing.

## Order and where scores land
1. G3 pre-test, draws 0-19 (seed 173, n 300, g3_pretest_s190 recipe, fly_all.sh scores after the last draw): g3_pretest/SCORE_KEY1.txt, SCORE_KEY2.txt, run_*/g3_checks.json, key2/*.json, progress.txt.
2. G5: g5_modes/ (G5.1 stick_steps acro/stab, G5.2 stick_pos_steps altctl/posctl, G5.7 mode_switch10 s1-s3, scored `*.key1.txt`/`*.key2.txt`; probe rows auto_land10_typ, auto_tour_typ/harsh -> `*.check.txt`), g510_stab/ (INDI only, 3 seeds, `*.score_key1.txt`/`score_key2.txt`; PID stab reference not re-flown), g5/ (auto_tour, auto_land10, hold_wind x3), g55/ (24 rows), events/. Scores as in freeze9_s183/G5_SCORES.md commands: `g55/*.check.txt`, `g55/key2_g55.txt`, `g5/*.check.txt`, `g5/*.g53.check.txt`, `g5/g53_hold_check.txt`, `g5/key2_*.txt`, `events/*.txt`.
3. G4: 18 rows into g4/ (gate_g4.sh fly), then g4_score.sh in docker (score_all.sh equivalent: g4_table.md, key1/key2 stdout + Q19, guard_indi.jsonl, chatter_stdout.txt with RAW=g4/chatter_cruise_raw.txt, Q20 guard `guard_q20_key1_stdout.txt`, `guard_q20_key2_stdout.txt`, selftests). PID refs via symlink g4_pid -> freeze9_s183/g4_pid (PID firmware unchanged). Done marker g4/g4_score.done.
4. G2: g2o/ (8 ax3 cells + 16 xy cells, `*_margins.json`, `*_holes.txt` from g2o_fly.sh), g2s/ (rate, att spot cells), steps/ (G2-STEP 3 seeds x 3).

## Resume
`bash indi_flight/results/freeze10_s193/queue.sh N` from anywhere (N = first step 1-4, default 1), launched with the nohup setsid command above. Finished items (flight.ulg or margins JSON, G3 SCORING_DONE_MARK, g4_score.done) are skipped; a half-flown G3 draw resumes by itself (g3_done.json). Clear a finished item's done-file to re-run it. Stray containers: queue stops all running containers before each item.

## Estimate and caveats
About 20 G3 draws x 2 min plus scoring, ~45 G5 flights, 18 G4 x 1 min, ~35 G2 cells x 1.3 min: roughly 4-5 h total (estimate from freeze9 queue_status.tsv and g3_pretest_s190/progress.txt).
Unverified: G5 host scoring needs pyulog on the host (freeze9 did this); g4_score.sh path rewriting and G5 scoring blocks have not been run. Hole-report FAIL cells need a re-fly by hand as at freeze-9 (delete the cell, rerun the step).
