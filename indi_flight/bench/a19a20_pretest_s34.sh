#!/bin/bash
# S34 pre-test for A-19 (EKF2 declination/mag bias) and A-20 (baro autocal): 2 hover + 1 step_roll, speed 4, seed 1,
# same flags as B32 plus bench/a19a20_pretest_s34.params. Sequential, -t 300 wall timeout, no retry. Then the A-19
# script (copied next to the runs, writes there) and the A-14/A-20 check.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
R=indi_flight/results/a19a20_s34
mkdir -p $R
fly() { # scenario outdir
  t0=$(date +%s)
  indi_project/docker/run.sh -n a19a20_$(basename $2) -t 300 -- python3 indi_flight/bench/run_scenario.py --scenario $1 --controller pid_default --model quad5in --seed 1 --speed 4 --sched --sched-anchor --params indi_flight/bench/a19a20_pretest_s34.params --out $2 > $2_stdout.log 2>&1
  echo "$2 docker_rc=$? wall=$(( $(date +%s) - t0 ))s" >> $R/status.txt
}
fly hover $R/hover_r1
fly hover $R/hover_r2
fly step_roll $R/step_roll_r1
python3 indi_flight/bench/a14_close_check.py --out $R/a14_check.md $R/hover_r*/flight.ulg > $R/a14_check_stdout.txt 2>&1
echo "a14_check_rc=$?" >> $R/status.txt
echo ALL_DONE >> $R/status.txt
