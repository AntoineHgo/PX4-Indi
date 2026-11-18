#!/usr/bin/env bash
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi || exit 1
D=indi_flight/results/gnss_delay_key_s106
for spec in "M|250" "X|0"; do
  n=${spec%%|*}; g=${spec#*|}
  timeout 1000 indi_project/docker/run.sh -n gk_$n -t 900 -- python3 indi_flight/bench/run_scenario.py --scenario hover_long --controller indi_m3a --seed 1 --speed 4 --model quad5in --rate-hz 800 --sim v2 --gps-dly 250 --gnss-delay $g --out $D/$n > $D/$n.stdout.log 2>&1
  echo "$n exit=$?" >> $D/fly.out
done
echo done >> $D/fly.out
