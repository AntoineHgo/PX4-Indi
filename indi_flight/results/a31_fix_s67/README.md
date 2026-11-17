# A-31 fix (S67): disturbance wrench applied twice

## 1. Verification (before the fix)
- src/modules/simulation/gz_bridge/server.config line 14 loads gz-sim-apply-link-wrench-system for every world.
  gz_env.sh.in exports GZ_SIM_SERVER_CONFIG_PATH=$PX4_GZ_SERVER_CONFIG (= that file); run_scenario.py sources gz_env.sh.
- g15 disturbance.log: "system add attempt 0 ... data: true", i.e. a second instance was added at runtime. g15 gz.log has no
  ApplyLinkWrench lines (not informative). Direct two-instance proof is the flight result below (2.0x -> 1.0x); gz source not read.

## 2. Fix (indi_flight/bench/disturbance.py)
- New `--add-system {auto,yes,no}` (default auto): auto reads $GZ_SIM_SERVER_CONFIG_PATH, then $PX4_GZ_SERVER_CONFIG; if the file contains
  `apply-link-wrench` the runtime add is skipped and "ApplyLinkWrench already loaded by <path>, not added" is logged. Decision logged in disturbance.log. Docstring updated.
- In flight the log shows: "config check -> .../src/modules/simulation/gz_bridge/server.config; runtime add NO".
- Self-test: only bench/tests/test_disturbance_sizing.py exists; pytest is not installed on the host, NOT run (py_compile OK).

## 3. Re-fly (one at a time): `indi_flight/results/a31_fix_s67/fly.sh payload_add` then `... com_shift` (quad5in, indi, 800 Hz, seed 1, speed 4, g15 indi.params). Both rc=0.
Analysis: `analyse.py <dir> <profile>` run in the container (esc_status rpm^2, ground-truth attitude).

## 4. Results
| | before (g15) | after (a31) | applied |
|---|---|---|---|
| payload_add mean rpm^2 ratio (10..28 s vs -8..-1 s) | 1.497 (extra 0.497 mg) | 1.2488 (extra 0.249 mg) | 0.25 mg: PASS (0.5 % off) |
| com_shift balancing torque (rpm^2 pair diff, scaled to g15 0.0898 N m) | 0.0898 | ~0.0439 (diff 34.1e6 vs 69.7e6 rpm^2) | 0.0448: PASS (2 % low) |
Note: the torque after is scaled from the g15 number (same airframe, same method), not recomputed from arm geometry.
- com_shift roll excursion at onset+26 s: GONE. Roll in +25..+28 s: -0.1..+0.2 deg (before: -24.6..+86.8 deg). Onset window -2.7..+0.8 deg (before -5.4..+2.1);
  clear window (+28..+31) -1.0..+2.5 deg (before -4.3..+2.8). So the 26 s event was a side effect of the double instance. Its exact mechanism is UNVERIFIED
  (not separated by the sim-time stamps of disturbance.csv, which was not re-examined; no gap check done); it did not recur in a single run (n=1, speed 4), so a rare event cannot be excluded.
- Verdict: A-31 closed on the evidence of 2 flights. Every g15 / earlier disturbance result (all profiles, incl. gust_x, gust_diag, torque_steps) was doubled and must be re-flown.
