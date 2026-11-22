# Harness defect run 039 (S208, Q27 item 8 and item 6)

## Cause
- `bench/run_scenario.py` (land block, ~l.1352-1365; old line `sim.run(None, sp=pos_sp if a.stick_mode ...)`): after NAV_LAND the runner kept sending the stick *neutral* sample.
- With `--stick-pilot` (stabilized/acro draws, `make_pilot_sp` l.702-735) the altitude pilot moves the throttle stick away from 500 to hold altitude (039: z 399-408 up to the land command, `run_039/sticks.csv`), then the neutral sample returns it to 503/500 about 0.5 s after the command.
- That 0.1 throttle-stick jump is read as a pilot override (px4.log: `Landing at current position` then `Pilot took over using sticks`): LAND -> POSCTL, vehicle hovers until the 150 s wall timeout.
- Why only 039: the other 297 completed runs have |z jump| small or are position-mode (no sticks); 039 is a stabilized draw whose pilot sat at z 400 (mass 0.70, hover offset) at the land command. The trigger (stick jump) is consistent with the logs, not isolated by an A/B.
- Scoring: `g3_run.py:288-315` classifies it `aborted`, `g3_chain.sh` scored it UNSCORED/SCORE_PENDING (metrics.json absent); with metrics present an aborted run could have reached a verdict.

## Fix (files)
- `bench/run_scenario.py`: after NAV_LAND in stick modes, repeat exactly the last stick sample sent (no re-centre, no pilot correction). Position/offboard modes unchanged.
- `bench/g3_run_status.py` (new): `invalid_reason(run_dir)` from run.json (exit_status, error, g3_outcome) and g3_done.json (outcome); missing status = invalid.
- `bench/g3_score.sh` (key 1): invalid run -> `g3_checks.json` `{"invalid": true, "pass": null}`, no scoring.
- `bench/g3_checks_key2.py` (key 2): same, before `load_run`.
- `bench/g3_chain.sh` `score()`: key 1/key 2 label `INVALID` in `chain_score.json` and `SCORES.tsv` (not pass, not FAIL, no failing items); key 2 INVALID json written for an invalid run.
- Item 6: `bench/g3_score.sh` line `python3 "$B/g3_checks.py" ... $args --skip-nav-change --json ...` now always passes `--skip-nav-change` (covers `g3_chain.sh start/rescore` and `g3_score_docker.sh`). Not re-scored for old campaigns. The `--skip-nav-change` flag is not in the args line printed for key 2 (key 2 has its own handling).

## Self-test
`python3 indi_flight/bench/tests/test_g3_harness_abort.py`: 3 tests. Before the scorer changes (stash of g3_score.sh and g3_checks_key2.py) test_key1_invalid FAILED (no g3_checks.json for an aborted run; key 2 would crash/not mark invalid); after: all PASS. The old scorer on an aborted run with metrics present is not exercised by a real ulog (UNVERIFIED).

## Flight (1 run)
`indi_039/` : `g3_chain.sh start ... 39 39 --speed 1` (INDI, speed 1, same tooling as g3_refly_s199). Outcome ok, 105 s, `Landing detected`, `Disarmed by landing`, run.json error none. Scored key 1 pass, key 2 pass (also exercises the new scorer path with --skip-nav-change). Single flight; the pre-fix speed-1 run 039 aborted in both stacks (g3_refly_s199/SUMMARY.md). PID not re-flown. flight.ulg untracked (ignored).
