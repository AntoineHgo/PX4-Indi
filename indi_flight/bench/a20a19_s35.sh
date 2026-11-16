#!/bin/bash
# S35: A-20 closing set (15 hovers, SENS_BAR_AUTOCAL 0 alone, speed 4, seed 1, B32 flags) then A-19 pre-test
# (2 hovers, EKF2_MAG_TYPE 1 heading-only + declination 2.62). Sequential, -t 300 wall timeout, no retry.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
R=indi_flight/results/a20a19_s35
mkdir -p $R/a20 $R/a19
fly() { # params outdir
  t0=$(date +%s)
  indi_project/docker/run.sh -n s35_$(basename $(dirname $2))_$(basename $2) -t 300 -- python3 indi_flight/bench/run_scenario.py --scenario hover --controller pid_default --model quad5in --seed 1 --speed 4 --sched --sched-anchor --params $1 --out $2 > $2_stdout.log 2>&1
  echo "$2 docker_rc=$? wall=$(( $(date +%s) - t0 ))s" >> $R/status.txt
}
for i in $(seq 1 15); do fly indi_flight/bench/a20_close_s35.params $R/a20/r$i; done
python3 indi_flight/bench/a14_close_check.py --out $R/a20/a14_check.md $R/a20/r*/flight.ulg > $R/a20/a14_check_stdout.txt 2>&1
echo "a14_check_rc=$?" >> $R/status.txt
echo A20_DONE >> $R/status.txt
for i in 1 2; do fly indi_flight/bench/a19_magtype_s35.params $R/a19/hover_r$i; done
echo ALL_DONE >> $R/status.txt
