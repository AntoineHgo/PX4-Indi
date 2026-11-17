#!/usr/bin/env bash
# S67 A-31 re-fly: same as g15_dist_s66/fly.sh but ONE profile at a time. usage: fly.sh payload_add|com_shift  (run from repo root)
G=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/g15_dist_s66
O=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/a31_fix_s67
sc=$1
indi_project/docker/run.sh -n s67d_$sc -t 900 -- python3 indi_flight/bench/run_scenario.py --scenario $sc \
  --controller indi --model quad5in --sim v2 --rate-hz 800 --seed 1 --speed 4 \
  --params $G/indi.params --out $O/$sc > $O/$sc.stdout 2>&1; echo "$sc rc=$?" >> $O/done.txt
