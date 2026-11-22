# G3 re-fly batch S199 (failure classification of g3_campaign_f10)

Purpose: apply the two pre-classification rules to the campaign failures (`../g3_campaign_f10/README.md` "Verdict", `FAILS_S199.md`):
(1) re-fly the index at speed 1, (2) fly the PID reference of the same draw (scenario, seed, plant) at speed 1. 8 indices, 16 flights, serial.

| idx | why |
|---|---|
| 245 | C1 loss of control (unscored abort) |
| 264 | C3 loss of control (unscored abort) |
| 008 | class A, 11 Hz q line |
| 240 | C1 class B |
| 283 | class A corner |
| 239 | Latin-hypercube class B with the largest key-2 amplitude (p@2Hz 54 dps; key 1 52 dps) |
| 046 | class D with the largest amplitude (key 1 p 15 dps; 067 ties at 15 dps, 046 taken as first) |
| 039 | harness artefact (LAND overridden by sticks) |

Why a wrapper: `g3_chain.sh` flies contiguous ranges, not lists, so each index gets its own chain dir `indi_NNN/`.

## Commands (repo root)
- Whole batch (detached): `setsid nohup bash indi_flight/results/g3_refly_s199/refly_all.sh >/dev/null 2>&1 </dev/null &`
- Per index, INDI: `bash indi_flight/bench/g3_chain.sh start indi_flight/results/g3_refly_s199/indi_NNN i i --speed 1` (flies and scores both keys)
- Per index, PID: `python3 indi_flight/results/g3_refly_s199/fly_pid_run.py i` (`--dry` checks only), then `g3_score_docker.sh pid_NNN` (key 1)
  and `g3_checks_key2.py` with the key-1 args (key 2), as `../g3_pretest_s187/pid_refs/fly_all_pid.sh`.
- `fly_pid_run.py` is the s187 copy: draw asserted equal to `../g3_campaign_f10/run_NNN/g3_draw.json`; argv equality ignores controller and
  `--speed` (campaign INDI ran at speed 4), and is also checked, strictly except controller, against the speed-1 INDI re-fly `indi_NNN/run_NNN`
  when it exists (always, in this batch order). A mismatch on either aborts the PID flight. PID base params as s187 (`pid_base.params` there).

## Resume / timeouts
Rerun the same wrapper command: an index is skipped when `indi_NNN/CHAIN_FINISHED` / `pid_NNN/DONE` exist; a half PID run is moved to
`run_NNN.incomplete_*`. Wrapper waits up to 1 h for a foreign chain lock. Wall clock: INDI chain 3300 s (then `stop --now`), PID flight 1700 s.

## Outputs
`progress.txt` (log), `DONE` (end of batch), `indi_NNN/` (chain dir: run_NNN, chain_score.json, SCORES.tsv), `pid_NNN/` (run_NNN, SCORE_KEY1.txt,
SCORE_KEY2.txt, key2/, stream.txt), `chain_start_NNN.txt`.

## Launch record
Wrapper pid 3600096 (shell; child of setsid), started 2026-11-22 18:18:49. Expected end about 19:05 to 19:15 (16 flights plus scoring).
