# G3 robustness campaign at FREEZE-10 (300 runs)

Purpose: the G3 campaign of GATES.md "### 3. G3 Robustness campaign" (amended S197, Q24 B GNSS mismatch +-50 ms), flown
serially by the detached flight chain `bench/g3_chain.sh`, independently of any Claude session, resumable.

## What is flown
- Draw: `bench/g3_run.py --seed 173 --n 300`, indices 0-299 = the whole campaign draw of `g3_sample.campaign(173, 300)`:
  0-239 Latin hypercube, 240-299 corners C1-C6 (10 each), 300 distinct sampler and gz seeds. Indices 0-19 are the
  pre-test draws (`../g3_pretest_q24_s197/`, `../freeze10_s193/g3_pretest/`); they are flown again here so that this
  directory is self-contained evidence.
- Command per index i (repo root), as `../g3_pretest_q24_s197/fly_all.sh`:
  `timeout 1700 indi_project/docker/run.sh -n g3c_NNN -t 1500 -- python3 indi_flight/bench/g3_run.py --seed 173 --n 300
  --start i --stop i --base-params indi_flight/results/g5_freeze_s157/params.params --out-root indi_flight/results/g3_campaign_f10
  --timeout-s 1200 --speed 1.0` (`--speed 1.0` leaves the runner argv unchanged; the chain option `--speed F` is
  pinned per directory in `chain_speed` and reported in `chain_status.json`).
- Freeze: FREEZE-10 firmware, gate binary sha256 d220e19315c2798aa18a1bab6ce7300cd0f6eff14d43273d5064c06009d46076 (as in
  every pre-test run, `run.json` `provenance.binary_sha256`), config `g5_freeze_s157/params.params`. At the first start
  the chain pins the binary, the runner/scorer inputs and the docker image (`chain_freeze.sha256`, `chain_image_id`); a
  change before a flight, or a run whose `run.json` records another binary, halts the chain.

## Operate (any cwd, from the repo root shown)
- Start or resume: `bash indi_flight/bench/g3_chain.sh start indi_flight/results/g3_campaign_f10 0 299`
  (later starts reuse the range). Refuses if a chain runs, if `CHAIN_HALTED` exists, or if the binary is not the gate
  binary (`--allow-binary SHA` overrides on a fresh directory only).
- Status: `bash indi_flight/bench/g3_chain.sh status` (lock held = flying; "DEAD" = status says running, no lock).
- Stop after the current run and its scoring: `... stop`; at once (kills the flight and its container): `... stop --now`.
  The interrupted index is flown again from scratch on the next start (its partial directory goes to `partial/`).
- Score runs that have no score (scoring failed or interrupted): `... rescore` (refused while the chain flies).
- The chain ignores `indi_flight/STOP` (supervisor stop file) and never runs git: the orchestrator commits finished runs.

## Files
- `run_NNN/`: runner output (`g3_done.json` = finished: outcome ok, aborted = flight failure, void = validity failed),
  `chain_key1.txt`, `g3_checks.json` (key 1, `bench/g3_score.sh` / `g3_checks.py`), `chain_key2.txt`, `key2/run_NNN.json`
  (key 2, `bench/g3_checks_key2.py`, same per-run args), `chain_score.json` (both verdicts and failing items),
  `SCORE_PENDING` (scoring missing, re-run `rescore`), `CHAIN_FAILED` (no finished run after 2 attempts).
- `SCORES.tsv`: one line per finished run (idx, outcome, key 1, key 2, failing items, key 2 col 5).
- `progress.txt` (append-only: attempts with rc and duration, scores, cycle time, start/stop/halt/finish),
  `chain_status.json` (state, pid, counts, key pass counts, binary, ETA), `chain.log`, `stream_N.txt` (ignored).
- `CHAIN_HALTED` (reason; the chain stopped itself), `CHAIN_FINISHED` (every index finished or CHAIN_FAILED).
- `partial/`, `.score_tmp/` are scratch (ignored, not evidence).

## Failure handling
- A flight with rc != 0, a timeout or no `g3_done.json` is retried once; then `CHAIN_FAILED` and the next index. An
  aborted run is a flight result, not retried. A void run is not retried (GATES: re-fly, not a failure; the
  orchestrator decides).
- Circuit breaker: 3 failed or void indices in a row halt the chain (most likely docker/host trouble, not a controller
  result); their `CHAIN_FAILED` markers are removed so a restart flies them again. Also halts on a freeze mismatch and on
  free disk < 5 GB (one run is ~130 MB, 300 runs ~40 GB).
- On `CHAIN_HALTED`: read it and `progress.txt`/`stream_N.txt` of the last indices, fix the cause, `rm CHAIN_HALTED`,
  start again. To re-fly a `CHAIN_FAILED` index: remove that marker (and `CHAIN_FINISHED`), start again.

## Verdict
After `CHAIN_FINISHED`: rescore if any run is unscored, then the GATES "Campaign pass" rule (0 LOC, 0 sustained
oscillation, items 3-6 in >= 95 % of valid runs, every miss explained; Q24 B rule for draws shared with PID).
Key 2 column 5 (G4 command chatter) is not part of the G3 verdict.
