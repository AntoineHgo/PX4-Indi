#!/usr/bin/env bash
# Serial pre-test: two short SITL hover flights, delay hooks off (d0) and 5 ms (d5). Run from repo root.
set -u
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi || exit 1
D=indi_flight/results/delay_pretest_s102
for spec in "d0|--dly-act 0 --dly-imu 0" "d5|--dly-act 5 --dly-imu 5"; do
  name=${spec%%|*}
  flags=${spec#*|}
  indi_project/docker/run.sh -n dly_$name -t 900 -- python3 indi_flight/bench/run_scenario.py --scenario hover_long --controller indi_m3a --seed 1 --speed 4 --model quad5in --rate-hz 800 --sim v2 $flags --out $D/$name > $D/$name.stdout.log 2>&1
  echo "$name exit=$?"
done
