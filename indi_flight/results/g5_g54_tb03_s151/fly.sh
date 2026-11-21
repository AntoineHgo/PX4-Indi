#!/usr/bin/env bash
# S151 G5.4 take-off/land probe at MC_INDI_POS_TB 0.3 (D-GAP-G510 overturn test: ramp/landing edge). Repo root.
D=indi_flight/results/g5_g54_tb03_s151
for SC in auto_land10 auto_tour; do
  indi_project/docker/run.sh -n s151g54$SC -t 900 -- python3 indi_flight/bench/run_scenario.py --controller indi \
    --model quad5in --seed 1 --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 \
    --params indi_flight/results/g5_g510_s150/params_tb03.params --scenario $SC --out $D/$SC > $D/$SC.stdout.log 2>&1
  indi_project/docker/run.sh -n s151c$SC -t 240 -- python3 indi_flight/bench/auto_smoke_check.py $D/$SC \
    --json $D/$SC/check.json > $D/$SC.check.txt 2>&1
done
echo "g54 done"
