#!/bin/bash
# A-14 closing test (S28): waits for the B26 speed-1 batch, installs the baro reference-altitude model
# (indi_flight/sim/staged/quad5in_base_model_a14.sdf), flies 1 pre-test hover, checks it, then 15 same-seed hovers
# at speed 4 (--sched --sched-anchor, same as B26) and checks them. Sequential, -t 300 wall timeout, no retry.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
R=indi_flight/results/a14_close_s28
mkdir -p $R
for i in $(seq 240); do grep -q BATCH_DONE indi_flight/results/g16_sched_set_s26/speed1/status.txt 2>/dev/null && break; sleep 30; done
grep -q BATCH_DONE indi_flight/results/g16_sched_set_s26/speed1/status.txt || { echo "B26_NOT_DONE" >> $R/status.txt; exit 1; }
cp indi_flight/sim/staged/quad5in_base_model_a14.sdf indi_flight/sim/models/quad5in_base/model.sdf
echo "model installed $(date -Is)" >> $R/status.txt
fly() {
  t0=$(date +%s)
  indi_project/docker/run.sh -n a14close_$1 -t 300 -- python3 indi_flight/bench/run_scenario.py --scenario hover --controller pid_default --model quad5in --seed 1 --speed 4 --sched --sched-anchor --out $R/$1 > $R/$1_stdout.log 2>&1
  echo "$1 docker_rc=$? wall=$(( $(date +%s) - t0 ))s" >> $R/status.txt
}
fly pretest
python3 indi_flight/bench/a14_close_check.py --out $R/pretest_check.md $R/pretest/flight.ulg > /dev/null 2>&1 \
  || { echo "PRETEST_FAIL (see pretest_check.md)" >> $R/status.txt; exit 1; }
echo PRETEST_PASS >> $R/status.txt
for i in $(seq 1 15); do fly r$i; done
python3 indi_flight/bench/a14_close_check.py --out $R/check.md $R/r*/flight.ulg > /dev/null 2>&1
echo "BATCH_DONE check_rc=$?" >> $R/status.txt
