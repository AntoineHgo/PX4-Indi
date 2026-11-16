#!/bin/bash
# G1.6 set with the sim-time player (T55): hover, step_roll, traj_lemniscate, 5 identical-seed runs each,
# --sched --sched-anchor, at speed 4 then speed 1. Sequential, -t 300 wall timeout per run, no retry (a failure is data).
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
for sp in 4 1; do
  R=indi_flight/results/g16_sched_set_s26/speed$sp
  mkdir -p $R
  for sc in hover step_roll traj_lemniscate; do
    for r in r1 r2 r3 r4 r5; do
      t0=$(date +%s)
      indi_project/docker/run.sh -n g16set_s${sp}_${sc}_$r -t 300 -- python3 indi_flight/bench/run_scenario.py --scenario $sc --controller pid_default --model quad5in --seed 1 --speed $sp --sched --sched-anchor --out $R/$sc/$r > $R/${sc}_${r}_stdout.log 2>&1
      echo "$sc $r docker_rc=$? wall=$(( $(date +%s) - t0 ))s" >> $R/status.txt
    done
  done
  echo BATCH_DONE >> $R/status.txt
done
