#!/bin/bash
# S103 G5 pre-test: thrust gap 0.85 (all motors, from "up") in manual POSCTL, neutral sticks. Run from repo root.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
D=indi_flight/results/g5_posctl_s103
indi_project/docker/run.sh -n s103p -t 420 -- python3 indi_flight/bench/run_scenario.py --scenario s5_gap085_posctl --stick-mode posctl --controller indi_s98 --model quad5in --seed 1 --speed 4 --sim v2 --params $D/gap.params --out $D/run > $D/stdout.txt 2>&1
echo "exit=$?"
indi_project/docker/run.sh -n s103c -t 300 -- python3 indi_flight/bench/s5_gap_check.py $D/run > $D/gap_check.out 2>&1
echo "check exit=$?"
