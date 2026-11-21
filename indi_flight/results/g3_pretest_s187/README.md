# G3 pre-test re-fly on the Q22 box (S187)

Purpose: the 20-run G3 pre-test must be clean before the 300-run flight chain. Re-fly of S173 (g3_pretest_s173/fly.sh) on the new Q22 draws
(G1 error x[0.8,1.2] log-uniform per axis; tau_up/tau_down x[0.5,3]). Run 17 of S173 (e 1.52) was out of box; it is replaced by new draw 17.

Source draws: `bench/g3_sample.py campaign(173, 300)` indices 0-19, read by `bench/g3_run.py` (sampler already fixed and second-keyed, see
results/g3_box_s187/README.md and KEY2_REVIEW.md; reference copies in results/g3_box_s187/pretest_draws). Each run dir gets g3_draw.json with the
draw actually flown. Dry-check done before launch: `g3_run.py ... --dry-run` prints 20 commands (run 0: tau=0.79,tau_up=0.633 -> tau_up 0.50 x nominal,
gps-dly/gnss-delay 152, vib-acc 11.23, imu-noise-scale 4.0; run 1: gps-dly 86, gnss-delay 73), nothing written.

Config: freeze-9 firmware as in the px4-indi-sim image used for the S173/G5 runs; params results/g5_freeze_s157/params.params (contains MC_INDI_POS_EN 1).
Plant/noise flags come from the draw (g3_run adds --gps-dly/--gnss-delay/--vib-acc/--vib-gyr/--imu-noise-scale), not from a fixed command line.

Command (per run i, from `fly_all.sh`):
```
timeout 1700 indi_project/docker/run.sh -n g3p187_$i -t 1500 -- python3 indi_flight/bench/g3_run.py --seed 173 --n 300 --start $i --stop $i \
  --base-params indi_flight/results/g5_freeze_s157/params.params --out-root indi_flight/results/g3_pretest_s187 --timeout-s 1200 > stream_$i.txt
```
Launched chained behind the G5.10 batch (shell pid 804821): `nohup setsid bash -c 'while kill -0 804821 ...; do sleep 30; done; bash .../fly_all.sh' > batch.nohup.log`.
Progress: progress.txt (one line per run, BATCH_END, SCORING_DONE); FLY_DONE when flying ends.

Expected wall time: S173 took 103 s/run (09:39-10:14, 20 runs, 34.5 min), so about 35 min flying plus about 5 min scoring, after the G5.10 batch ends.

Resume a partial batch: `bash indi_flight/results/g3_pretest_s187/fly_all.sh [first] [last]` (skips runs with g3_done.json; stops stray px4-indi-g3p187_* containers).
Never run it while another simulation is running. `SKIP_SCORE=1` skips scoring. Score only: see below.

Scoring (end of fly_all.sh, non-interactive, per-run args derived by g3_score.sh from run.json/metrics.json/g3_draw.json):
- Key 1: `bash indi_flight/bench/g3_score_docker.sh indi_flight/results/g3_pretest_s187 > SCORE_KEY1.txt` (g3_checks.py; per-run g3_checks.json/txt; PASS/FAIL lines appended).
- Key 2: for each "run_NNN <args>" line of SCORE_KEY1.txt: `docker/run.sh -- python3 indi_flight/bench/g3_checks_key2.py <run dir> <args> --out indi_flight/results/g3_pretest_s187/key2` -> SCORE_KEY2.txt, key2/run_NNN.json.
Note: the "rescore_v3/v4" items in results/g3_excursion_s186 are output directories (key 2 / key 1), not scripts; the scorers are g3_checks.py (key 1, includes D-G3-ZREF) and g3_checks_key2.py.
Scoring was not run yet. Explain every failure before counting (S173 README).
