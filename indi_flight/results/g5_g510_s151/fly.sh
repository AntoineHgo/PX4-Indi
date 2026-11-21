#!/usr/bin/env bash
# S151 G5.10 sat_sustained, 3 seeds, TB 0.3 + kMaxBlend 0.5 (firmware 003e25c6d4), parallel (G5.10 probe, STATE 4a).
# Run from repo root after the G2 cells (never beside them).
D=indi_flight/results/g5_g510_s151
for S in 1 2 3; do
  indi_project/docker/run.sh -n s151g510s$S -t 700 -- python3 indi_flight/bench/run_scenario.py --controller indi \
    --model quad5in --seed $S --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 \
    --params indi_flight/results/g5_g510_s150/params_tb03.params --scenario sat_sustained --out $D/s$S > $D/s$S.stdout.log 2>&1 &
  sleep 20
done
wait
for S in 1 2 3; do
  indi_project/docker/run.sh -n s151c$S -t 240 -- python3 indi_flight/bench/g510_check.py $D/s$S --json $D/s$S/g510.json > $D/s$S.check.txt 2>&1
done
echo "g510 batch done"
