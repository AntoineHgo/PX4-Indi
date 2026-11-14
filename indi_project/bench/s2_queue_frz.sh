#!/usr/bin/env bash
# Runs the s2_recheck_v1 frozen control variant after bench/s2_after_rebuild.sh (recheck then r1f) has exited,
# so it flies on the same px4_sitl_default binary and does not share the CPU with r1f. Rebuild only after this.
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project
while pgrep -f 's2_after_rebuild.sh|s2_pid_tune_r1f.sh' > /dev/null; do sleep 60; done
exec "$P/results/s2_recheck_v1/run_frz.sh" > "$P/results/s2_recheck_v1/run_frz.log" 2>&1
