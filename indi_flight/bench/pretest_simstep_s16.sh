#!/bin/bash
# D-SIM-STEP pre-test (S16): 3 PID flights on the 1.25 ms world, speed 4, sequential, 300 s wall timeout each.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
R=indi_flight/results/pretest_simstep_s16
mkdir -p $R
for spec in "hover 800" "hover 400" "step_roll 800"; do
  set -- $spec
  d=$R/$1_r$2; t0=$(date +%s)
  indi_project/docker/run.sh -n pre_s16_$1_$2 -t 300 -- python3 indi_flight/bench/run_scenario.py --scenario $1 --controller pid_default --model quad5in --seed 1 --speed 4 --rate-hz $2 --out $d > $R/$1_r$2_stdout.log 2>&1
  echo "$1 rate=$2 docker_rc=$? wall=$(( $(date +%s) - t0 ))s" >> $R/status.txt
done
