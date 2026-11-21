# G3 pre-test PID reference flights (S188)

Purpose: owner rule, when a gate test fails, first fly the PID reference of the same scenario and seed. If PID shows the same failure
(item 2 sustained p/q oscillation), it goes to the owner as a possible test defect, not to an INDI cause search.

Runs (priority order): 10, 16, 0, 5, 17, 2, 3, 8, 9, 13 (the 10 INDI failures of g3_pretest_s187, all item 2). Serial.
Draw: master seed 173, n 300, `g3_sample.campaign(173, 300)` index i, including plant variant, delays, vibration, faults, wind.
`fly_pid_run.py` asserts the draw equals `../run_NNN/g3_draw.json` and that the run_scenario argv equals the INDI run's argv except
controller (`pid_default` instead of `indi`) and the output/params paths. Dry check for run 10 (stick_zsine_o6, stabilized, seed 170727245,
sim-seed 1054852865, model-variant tau=1.07848,tau_up=0.747543,mass=1.17896,ixx..izz, dly 2/2, erpm-drop 0.12643, vib 11.96/0.098,
gps-dly 248, gnss-delay 189): ARGV_EQUAL_EXCEPT_CONTROLLER True.

Differences to the INDI run (by design): `MC_RATE_CTL_TYPE` not set, no MC_INDI_* params (g1_ctrl_mult only scales MC_INDI_G1_*, so it is
not applied to PID). `pid_base.params` = results/g5_freeze_s157/params.params minus all MC_INDI_* keys; that file holds only MC_INDI_*
keys, so the base is empty (comments only). The S185 pid_base.params (run_017_pid_s185) was never committed; it is not recoverable, this is its
documented equivalent (UNVERIFIED identical).

Commands (repo root):
- one run: `indi_project/docker/run.sh -n g3pid188_10 -t 1000 -- python3 ...` is issued by `python3 indi_flight/results/g3_pretest_s187/pid_refs/fly_pid_run.py 10`
  (subprocess timeout 1100 s; `--dry` prints the command and the equality check without flying).
- batch: `bash indi_flight/results/g3_pretest_s187/pid_refs/fly_all_pid.sh` (per-run `timeout 1700`, stops only containers `g3pid188_*`).
- launched chained after the G5 modes batch (waiter pid 965041 waits on 851312), log `batch.nohup.log`.
Expected duration: about 103 s per run, about 17 min for 10 flights, plus scoring a few minutes.

Outputs: `run_NNN/` (same layout as the INDI runs), `progress.txt`, `stream_N.txt`, `SCORE_PID_KEY1.txt`, `SCORE_PID_KEY2.txt`, `key2/`, `DONE` (last step).
Validity: g3_run.finalize uses run_validity with the `pid_*` alias (controller pid: MC_INDI_EN 0, no INDI rate samples); a `void` outcome means wrong controller.
Scoring: key 1 `g3_score_docker.sh pid_refs` (g3_score.sh, window = last 3 s hold, `--wind`/`--sag` from g3_draw.json, same derivation as the INDI runs),
key 2 `g3_checks_key2.py` with the same per-run args from the key-1 lines.

Resume: rerun `fly_all_pid.sh`; runs with g3_done.json are skipped, an unfinished run dir is renamed `run_NNN.incomplete_<time>` and reflown.
Run a single index: `fly_pid_run.py IDX` (fails if `run_IDX` exists). Scoring only: run the script after the flights exist (it skips flown runs).
Compare against INDI: `../run_NNN/g3_checks.json` vs `run_NNN/g3_checks.json` (item 2 axes p/q).
