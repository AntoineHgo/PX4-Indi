#!/bin/bash
# S48 sequential M3a validation flights (host). usage: bash fly.sh
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
D=indi_flight/results/stage2_s48/m3a_check
for n in tc33_p8 tc33_p3; do
  indi_project/docker/run.sh -n s48$n -t 900 "python3 indi_flight/bench/run_scenario.py --scenario hover_long --controller indi_m3a --seed 1 --speed 4 --model quad5in --params $D/$n.params --out $D/$n" > $D/${n}_stdout.log 2>&1
  indi_project/docker/run.sh -n s48p$n -t 600 "bash $D/post.sh $n 0.001" > $D/${n}_post.log 2>&1
done
echo ALLDONE > $D/done.txt
