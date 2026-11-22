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
  --timeout-s 1200 --speed 1.0`. g3_run.py passes `--speed` on to run_scenario.py only when it is not 1.0, so at 1.0
  the flown command is the pre-test one. The chain option `start --speed F` (default 1.0) is pinned per directory in
  `chain_speed` and reported in `chain_status.json`. The wall-clock timeouts (1700/1500/1200 s) are not scaled with F.
- **This campaign flies at speed 4** (owner decision 2026-11-22, evidence `speed_check/README.md`): first start
  `bash indi_flight/bench/g3_chain.sh start indi_flight/results/g3_campaign_f10 0 299 --speed 4`.
- Freeze: FREEZE-10 firmware, gate binary sha256 d220e19315c2798aa18a1bab6ce7300cd0f6eff14d43273d5064c06009d46076 (as in
  every pre-test run, `run.json` `provenance.binary_sha256`), config `g5_freeze_s157/params.params`. At the first start
  the chain pins the binary, the runner/scorer/model inputs, `build/px4_sitl_default/etc`, the gz plugins, `gz_env.sh`
  and the docker image (`chain_freeze.sha256`, `chain_image_id`). A change before a flight halts the chain; a run whose
  `run.json` records another binary (or none) is moved to `partial/` and halts it.
- **Until CHAIN_FINISHED, do not modify any file listed in `chain_freeze.sha256`, do not rebuild, and do not switch
  branches or check out over them**, even while the chain is stopped.

## Operate (any cwd, from the repo root shown)
- Start or resume: `bash indi_flight/bench/g3_chain.sh start indi_flight/results/g3_campaign_f10 0 299`.
  **The first start of this directory must be `0 299`**: the first start's range is the campaign range (`chain_range`).
  A later start may give a sub-range of it; `CHAIN_FINISHED` is written only when the whole campaign range is
  finished. Refuses if a chain runs, if `CHAIN_HALTED` exists, or if the binary is not the gate binary
  (`--allow-binary SHA` overrides on a fresh directory only). Only this directory is recorded in
  `indi_flight/logs/flight_chain.dir` (the supervisor reads it); check or smoke directories are not.
- Status: `bash indi_flight/bench/g3_chain.sh status` (lock held = flying; "DEAD" = status says running, no lock).
- Stop after the current run and its scoring: `... stop`; at once (kills the flight and its container): `... stop --now`.
  The interrupted index is flown again from scratch on the next start (its partial directory goes to `partial/`).
- Score runs that have no score (scoring failed or interrupted): `... rescore` (refused while the chain flies). It
  can exceed the 10 min tool timeout: run it in the background.
- The chain ignores `indi_flight/STOP` (supervisor stop file) and never runs git: the orchestrator commits finished runs.
  The supervisor launches no session while the chain holds its lock (unless `chain_status.json` of a running chain is
  over 1 h old: then a session is launched to diagnose a stuck chain); when it is free, the session prompt names the
  chain state (halted, finished, or stopped/died).

## Files
- `run_NNN/`: runner output (`g3_done.json`: outcome ok, aborted, or void = validity failed), `chain_class.txt` (the
  chain's class: ok, flight watchdog, other, void; see Failure handling),
  `chain_key1.txt`, `g3_checks.json` (key 1, `bench/g3_score.sh` / `g3_checks.py`), `chain_key2.txt`, `key2/run_NNN.json`
  (key 2, `bench/g3_checks_key2.py`, same per-run args), `chain_score.json` (both verdicts and failing items),
  `SCORE_PENDING` (scoring missing, re-run `rescore`), `CHAIN_FAILED` (no finished run after 2 attempts).
- `SCORES.tsv`: one line per finished run (idx, outcome with the chain class and reason, key 1, key 2, failing items,
  key 2 col 5) and per `CHAIN_FAILED` index (reason).
- `FAULTS.tsv`: one line per infra attempt moved to `partial/` and per `CHAIN_FAILED` (time, idx, attempt, rc, partial
  path, reason).
- `progress.txt` (append-only: attempts with rc and duration, scores, cycle time, start/stop/halt/finish),
  `chain_status.json` (state, pid, counts, key pass counts, binary, ETA), `chain.log`, `stream_NNN.txt` (ignored).
- Key 1 runs `g3_score.sh` on `.score_tmp/` holding a symlink to the one run, so the `log` field of `g3_checks.json`
  reads `.../g3_campaign_f10/.score_tmp/run_NNN/flight.ulg` (same file as `run_NNN/flight.ulg`; the link is removed after
  scoring). The scorer is unchanged.
- `CHAIN_HALTED` (reason; the chain stopped itself), `CHAIN_FINISHED` (every campaign index finished or CHAIN_FAILED).
- `partial/`: every attempt moved aside (infra fault, interruption, wrong binary, void cleared by the breaker). It is
  evidence: commit its small files (`run.json`, `g3_done.json`, `chain_fault.txt` with the tails of the ignored
  `g3_stdout.txt` and stream); big files (ulog, logs, csv, rootfs) are ignored by the repo patterns. `.score_tmp/` is
  scratch (ignored).

## Failure handling
- Flight results (kept in place, counted, never retried by the chain): outcome ok; outcome aborted with an O-12 flight
  watchdog (`non-finite attitude or rate`, `tilt > 60 deg for 0.5 s`, `height < 0.3 m`,
  `> 3.0 m below hold altitude for 1.0 s`); and every other abort not on the infra list below ("other", e.g. `climb not
  finished`, `wall timeout in phase 'land'`, `takeoff rejected`, `arm rejected`, `no COMMAND_ACK`, `timeout waiting for
  'Ready for takeoff'`). The chain never excludes a failure: exclusion is the gate's class (a), with proof on the log.
- Infra faults (moved to `partial/`, flown once more, then `CHAIN_FAILED`; counted by the breaker): rc != 0, timeout or
  no `g3_done.json`; unreadable `g3_done.json`; aborts whose `error` is `px4 exited early ...`, `timeout ... waiting for
  'Startup script returned successfully'`, `gz sim exited early`, `timeout waiting for gz world`, `gz unpause failed`,
  `param set/show ... failed`, `no MAVLink heartbeat in 60 s`, the `no ATTITUDE for 10 s wall` stall watchdog, host
  exceptions raised by the runner (OSError and subclasses, subprocess errors, JSONDecodeError), or no ulog with no
  error. Any other exception (ValueError, ZeroDivisionError, KeyError, ...) is "other": a controller NaN can surface
  that way. Every attempt is in `FAULTS.tsv`.
- A void run is kept, not retried (GATES: re-fly, not a failure; the orchestrator decides); it counts for the breaker.
- On every start, finished runs are checked before being skipped: an infra fault is moved to `partial/` and flown
  again, a wrong or missing binary halts, an unscored run is scored.
- Circuit breaker: 3 infra-failed or void indices in a row halt the chain (most likely docker/host trouble, not a
  controller result); their `CHAIN_FAILED` markers are removed and void runs moved to `partial/`, so a restart flies
  them again. 10 "other" aborts in a row (more than one 10-run corner block) also halt the chain for a look (those runs stay counted as results). Also halts
  on a freeze mismatch and on free disk < 5 GB (one run is ~130 MB, 300 runs ~40 GB).
- On `CHAIN_HALTED`: read it and `progress.txt`, `FAULTS.tsv`, `stream_NNN.txt` of the last indices, fix the cause,
  `rm CHAIN_HALTED`, start again. To re-fly a `CHAIN_FAILED` index: remove that marker (and `CHAIN_FINISHED`), start
  again.

## Verdict
After `CHAIN_FINISHED`: rescore if any run is unscored, then the GATES "Campaign pass" rule (0 LOC, 0 sustained
oscillation, items 3-6 met in every valid run, no quota (GATES S94 decision 5; wording corrected S208, owner Q27 item 5); Q24 B rule for draws shared with PID).
Key 2 column 5 (G4 command chatter) is not part of the G3 verdict.
Speed rule (speed 4, `speed_check/README.md`): every item 1-2 failure, and every item 3-6 miss within the speed-1
same-seed spread of its threshold (altitude mean: up to 1.0 x the limit; horizontal RMS 0.16; roll/pitch mean 0.26),
is re-flown at speed 1 on the same index (its own chain dir, after CHAIN_FINISHED or with the campaign stopped) before
it is classified; report both flights, and classify on the speed-1 flight.
Every `FAULTS.tsv` row with the `no ATTITUDE for 10 s wall` stall needs a host cause in the evidence (suspend, load,
docker): a PX4 hang gives the same row.
