#!/usr/bin/env bash
# Paired INDI vs PID flights (quad5in, sim v2, 800 Hz, seed 1, speed 4). Run from the repo root.
O=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/indi_vs_pid  # absolute: disturbance.py runs in another cwd and must find the trigger file
fly() { # scenario controller
  indi_project/docker/run.sh -n cmp_$1_$2 -t 900 -- python3 indi_flight/bench/run_scenario.py --scenario $1 \
    --controller $2 --model quad5in --sim v2 --rate-hz 800 --seed 1 --speed 4 \
    --params $O/$2.params --out $O/$1_$2 > $O/$1_$2.stdout 2>&1; echo "$1 $2 rc=$?" >> $O/done.txt
}
for c in indi pid; do for grp in "step_roll step_pitch" "step_yaw torque_steps"; do
  ( for s in $grp; do fly $s $c; done ) &
done; done
wait
