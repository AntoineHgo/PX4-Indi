# G3 pretest S230: event-hover scenario, 4 flights (flight only, not scored)

Purpose: owner pre-test (a5) draw 0 INDI and PID reference, (b) FREEZE-10 baselines draws 262 and 283 (INDI), on the new
event-hover scenario (commits 9cd2a1cb1a, fda2630219; spec results/q33_tooling_s230/EVENT_HOVER_SPEC.md).

Binary pin: build/px4_sitl_default/bin/px4 sha256 903eae63ceb1... (checked at start; the PID script asserts it). No rebuild, no docker build.
Started 2026-11-26 00:46:39. Waiter pid (setsid bash chain.sh): 1547971 (also in waiter.pid).

Order (chain.sh), each with a wall timeout (INDI 1700 s, PID 1800 s), output under this folder:
1. indi_d0: `indi_project/docker/run.sh -n g3s230_indi_d0 -t 1500 -- python3 indi_flight/bench/g3_run.py --seed 173 --n 300 --start 0 --stop 0 --base-params indi_flight/results/g5_freeze_s157/params.params --out-root <dir>/indi_d0 --timeout-s 1200 --speed 1` (same as g3_chain.sh, no --samples, no --allow-binary)
2. pid_d0: `python3 fly_pid_s230.py` (adapted from g3_pretest_s227/pid_ref/fly_pid_s227.py: controller pid_default, base g3_pretest_s187/pid_refs/pid_base.params, draw asserted equal to indi_d0, argv asserted equal except controller) -> pid_d0/run_000
3. indi_d262: same as 1 with --start/--stop 262 -> indi_d262/run_262
4. indi_d283: same, 283 -> indi_d283/run_283

Status: `tail -n 5 indi_flight/results/g3_pretest_s230/STATUS.txt` (one START and one END line with exit code per run, then CHAIN_FINISHED).
Per-run console: stream_<run>.txt. Check pid alive: `ps -p 1547971`.
Expected wall time: about 3-4 min per flight (S227 flight was 2.5 min, plus 23 s event hover), roughly 15 min total, end about 01:00-01:05.

Next session: score all four with both keys (g3_checks.py via g3_score.sh and g3_checks_key2.py); nothing is scored here.
If a run ends with a nonzero exit the chain continues with the next run; check STATUS.txt.
