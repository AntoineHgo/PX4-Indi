# D-yawnu hover check (session 11)

Firmware d2fb64330f (YAW_CUT also filters the yaw rate in nu). Params: r2 c11
with YAW_CUT 2 Hz (`results/tuning/indi/r2f_yc2/c00/params`). Hover, seeds 1-3,
speed 1, 0 failures. Command:
`SCENARIOS=hover CONTROLLERS=indi_c11_yc2_yawnu SEEDS="1 2 3" SPEEDS=1 JOBS=3
NAME_TAG=yawnu PARAMS_FILE=$PWD/results/tuning/indi/r2f_yc2/c00/params
RESULTS_DIR=$PWD/results/yawnu_check_s11 FLAT_LAYOUT=1 bash bench/run_batch.sh`
(cwd indi_project). Analysis: `bench/effort_axes.py`, `bench/indi_terms.py`.

| | yaw tq std | yaw tq drms | yaw nu/G1 drms | motor-rate RMS (1/s) | hover pos RMS (m) |
|---|---|---|---|---|---|
| PID defaults (r2 c00, seed 1) | 0.0003 | 0.0000 | - | 0.037 | |
| INDI c11 YAW_CUT 2, before D-yawnu | 0.0005-0.0007 | 0.0003 | 0.00028 | 0.077-0.080 | |
| INDI c11 YAW_CUT 2, D-yawnu | 0.0005-0.0006 | 0.0000 | 0.00002-0.00003 | 0.041-0.043 | 0.017-0.024 |

The yaw chatter is gone. Hover motor-rate effort is ~1.1x PID's, below the
cost's 1.25 effort-penalty threshold (`bench/tune.py`), against ~2.1x before.
Hover only; tracking on the step scenarios with the new firmware is checked
by the run `results/tuning/indi/r2f_yawnu/` (same candidate, 5 tuning
scenarios x 3 seeds).
