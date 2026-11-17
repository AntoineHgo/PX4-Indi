#!/usr/bin/env bash
# G16 determinism batch: G2-STEP 400 Hz, seed 1, step_roll, quad5in, indi. Same params as S64 (results/g2_step_s64_400/indi.params).
# s4_r1..s4_r5: --speed 4, all 5 in parallel. s1_r1..s1_r3: --speed 1, 3 in parallel (wall timeout 2400 s).
G=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/g16_indi_s67
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/g2_step_s64_400/indi.params
run() { # $1=label $2=speed $3=wall timeout s
  O=$G/$1; mkdir -p $O
  indi_project/docker/run.sh -n s67g_$1 -t $3 -- python3 indi_flight/bench/run_scenario.py --scenario step_roll \
    --controller indi --model quad5in --sim v2 --rate-hz 400 --seed 1 --speed $2 \
    --params $P --out $O/step_roll_indi > $O/step_roll_indi.stdout 2>&1; echo "$1 speed$2 rc=$?" >> $G/done.txt; }
mkdir -p $G
run s4_r1 4 900 & run s4_r2 4 900 & run s4_r3 4 900 & run s4_r4 4 900 & run s4_r5 4 900 & wait
run s1_r1 1 2400 & run s1_r2 1 2400 & run s1_r3 1 2400 & wait
echo ALLDONE >> $G/done.txt
