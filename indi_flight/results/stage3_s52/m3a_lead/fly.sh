#!/bin/bash
# S52 roll M3a with the rate lead, ACT_TC 0.033, P8, AMP 0.001, seeds 1 and 2 (host). usage: bash fly.sh
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
D=indi_flight/results/stage3_s52/m3a_lead
for s in 1 2; do
  n=lead1_s$s
  indi_project/docker/run.sh -n s52$n -t 900 "python3 indi_flight/bench/run_scenario.py --scenario hover_long --controller indi_m3a --seed $s --speed 4 --model quad5in --params $D/lead1.params --out $D/$n" > $D/${n}_stdout.log 2>&1
  indi_project/docker/run.sh -n s52p$n -t 600 "bash $D/post.sh $n 0.001" > $D/${n}_post.log 2>&1
done
echo ALLDONE > $D/done.txt
