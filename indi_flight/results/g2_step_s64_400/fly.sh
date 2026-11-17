#!/usr/bin/env bash
# S64: G2-STEP 400 Hz reported run (not a pass condition), same binary as results/g2_step_s64 (360c9ae453), seeds 1-3.
G=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/g2_step_s64_400
step() { O=$G/steps_seed$2; mkdir -p $O
  indi_project/docker/run.sh -n s64q_$1_$2 -t 900 -- python3 indi_flight/bench/run_scenario.py --scenario $1 \
    --controller indi --model quad5in --sim v2 --rate-hz 400 --seed $2 --speed 4 \
    --params $G/indi.params --out $O/$1_indi > $O/$1_indi.stdout 2>&1; echo "$1 seed$2 rc=$?" >> $G/done.txt; }
for seed in 1 2 3; do ( for s in step_roll step_pitch step_yaw; do step $s $seed; done ) & done
wait; echo ALLDONE >> $G/done.txt
