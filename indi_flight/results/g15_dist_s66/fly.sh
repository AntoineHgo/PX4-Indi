#!/usr/bin/env bash
# S66: G1.5 disturbance-injector pre-test, quad5in, INDI, 800 Hz, speed 4, seed 1. Five profiles in parallel.
G=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/g15_dist_s66
fly() { indi_project/docker/run.sh -n s66d_$1 -t 900 -- python3 indi_flight/bench/run_scenario.py --scenario $1 \
  --controller indi --model quad5in --sim v2 --rate-hz 800 --seed 1 --speed 4 \
  --params $G/indi.params --out $G/$1 > $G/$1.stdout 2>&1; echo "$1 rc=$?" >> $G/done.txt; }
for sc in torque_steps gust_x payload_add gust_diag com_shift; do fly $sc & done
wait; echo ALLDONE >> $G/done.txt
