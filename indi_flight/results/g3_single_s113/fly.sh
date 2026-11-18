#!/bin/bash
# usage: fly.sh NAME CONTROLLER PARAMS MASS
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
R=indi_flight/results/g3_single_s113
MV=""; [ "$4" != "1.0" ] && MV="--model-variant mass=$4"
indi_project/docker/run.sh -n g3s_$1 -t 900 -- python3 indi_flight/bench/run_scenario.py --scenario stick_zsine_o6 --controller $2 --model quad5in --sim v2 --rate-hz 800 --seed 768592122 --sim-seed 680969658 --out $R/$1 --params $3 --stick-mode stabilized $MV > $R/$1.stdout 2>&1
echo "$1 rc=$?"
