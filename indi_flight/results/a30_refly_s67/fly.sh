#!/usr/bin/env bash
# A-30 re-fly: G2-STEP 400 Hz, seed 1, step_roll, quad5in, indi. Same params as S64 (results/g2_step_s64_400/indi.params).
# A and B: identical runs at --speed 4 in parallel. C: --speed 1, run after A/B so A/B load matches S64.
G=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/a30_refly_s67
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/g2_step_s64_400/indi.params
run() { # $1=label $2=speed $3=wall timeout s
  O=$G/$1; mkdir -p $O
  indi_project/docker/run.sh -n s67q_$1 -t $3 -- python3 indi_flight/bench/run_scenario.py --scenario step_roll \
    --controller indi --model quad5in --sim v2 --rate-hz 400 --seed 1 --speed $2 \
    --params $P --out $O/step_roll_indi > $O/step_roll_indi.stdout 2>&1; echo "$1 speed$2 rc=$?" >> $G/done.txt; }
run A 4 900 & run B 4 900 & wait
run C 1 2400
echo ALLDONE >> $G/done.txt
