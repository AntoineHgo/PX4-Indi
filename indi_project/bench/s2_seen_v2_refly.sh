#!/usr/bin/env bash
# Re-fly of three seen-set (entry, seed) pairs, all three controllers (D-v2-refly, O-12 setup faults):
# step_yaw seed 2 (estimator glitch in indi_v2 at 22:41, found by bench/glitch_scan.py; host overloaded by an
# offline replay beside the batch), hover seed 6 and mismatch_inertia seed 9 (pid_tuned sim stalled, wall timeout).
# The original runs are kept in results/s2_seen_v2/runs_suspended. s2_seen_v2.sh skips every run that has metrics.json.
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project
SEEDS="2 6 9" bash $P/bench/s2_seen_v2.sh >> $P/results/s2_seen_v2/run.log 2>&1
echo SEEN_V2_REFLY_DONE >> $P/results/s2_seen_v2/run.log
