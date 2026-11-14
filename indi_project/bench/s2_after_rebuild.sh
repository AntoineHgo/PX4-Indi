#!/usr/bin/env bash
# Session 33 chain, run detached after the px4_sitl_default rebuild: the v1 post-acceptance re-checks first
# (105 short runs), then the v2 PID tuning check on the FAC config (r1f). Sequential so the two batches do not
# share the CPU.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project
"$P/results/s2_recheck_v1/run.sh" > "$P/results/s2_recheck_v1/run.log" 2>&1
exec "$P/bench/s2_pid_tune_r1f.sh" > "$P/results/s2_tuning_r1f.log" 2>&1
