#!/bin/bash
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
D=indi_flight/results/stage5_s98
indi_project/docker/run.sh -n s98a -t 420 -- python3 indi_flight/bench/run_scenario.py --scenario s5_gap085 --controller indi_s98 --model quad5in --seed 1 --speed 4 --sim v2 --params $D/gap.params --out $D/A_gap085/run > $D/A.stdout.txt 2>&1
indi_project/docker/run.sh -n s98b -t 420 -- python3 indi_flight/bench/run_scenario.py --scenario s5_gap085_altctl --stick-mode altctl --controller indi_s98 --model quad5in --seed 1 --speed 4 --sim v2 --params $D/gap.params --out $D/B_altctl/run > $D/B.stdout.txt 2>&1
echo done > $D/fly.done
