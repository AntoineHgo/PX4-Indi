#!/bin/bash
# S53 ACT_TC sweep with lead 1 (plant tau 0.033), roll M3a, P8, AMP 0.001. usage: bash fly.sh TC SEED
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
D=indi_flight/results/stage3_s53/act_tc_sweep; tc=$1; s=$2; n=tc${tc}_s$s
indi_project/docker/run.sh -n s53$n -t 900 "python3 indi_flight/bench/run_scenario.py --scenario hover_long --controller indi_m3a --seed $s --speed 4 --model quad5in --params $D/tc$tc.params --out $D/$n" > $D/${n}_stdout.log 2>&1
indi_project/docker/run.sh -n s53p$n -t 600 "bash $D/post.sh $n 0.001" > $D/${n}_post.log 2>&1
echo DONE $n >> $D/done.txt
