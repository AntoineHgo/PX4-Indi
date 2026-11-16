#!/bin/bash
# A-14 closing test with the gz_bridge baro-elevation fix (4443079c0b, S31): 15 same-seed hovers at speed 4
# (--sched --sched-anchor, same as B26/B28), then a14_close_check.py over all. Sequential, -t 300 wall timeout, no retry.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
R=indi_flight/results/a14_bridge_s31
mkdir -p $R
fly() {
  t0=$(date +%s)
  indi_project/docker/run.sh -n a14bridge_$1 -t 300 -- python3 indi_flight/bench/run_scenario.py --scenario hover --controller pid_default --model quad5in --seed 1 --speed 4 --sched --sched-anchor --out $R/$1 > $R/$1_stdout.log 2>&1
  echo "$1 docker_rc=$? wall=$(( $(date +%s) - t0 ))s" >> $R/status.txt
}
for i in $(seq 1 15); do fly r$i; done
python3 indi_flight/bench/a14_close_check.py --out $R/check.md $R/r*/flight.ulg > /dev/null 2>&1
echo "BATCH_DONE check_rc=$?" >> $R/status.txt
