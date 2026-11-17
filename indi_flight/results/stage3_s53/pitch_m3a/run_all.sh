#!/bin/bash
# S53 pitch M3a (INJ_AX 2, csv axis 1), ACT_TC 0.05, lead 1, seeds 1 and 2 in parallel; then rebuild SITL at HEAD.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
D=indi_flight/results/stage3_s53/pitch_m3a
fly() { n=pitch_s$1
  indi_project/docker/run.sh -n s53$n -t 900 "python3 indi_flight/bench/run_scenario.py --scenario hover_long --controller indi_m3a --seed $1 --speed 4 --model quad5in --params $D/pitch_tc050.params --out $D/$n" > $D/${n}_stdout.log 2>&1
  indi_project/docker/run.sh -n s53p$n -t 600 "bash $D/post.sh $n 0.001" > $D/${n}_post.log 2>&1
  echo DONE $n >> $D/done.txt; }
fly 1 & fly 2 & wait
indi_project/docker/run.sh -n s53build -t 3600 'make px4_sitl_default' > $D/build.log 2>&1; echo "BUILD rc $?" >> $D/done.txt
echo ALLDONE >> $D/done.txt
