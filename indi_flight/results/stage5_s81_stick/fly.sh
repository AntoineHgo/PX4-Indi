#!/bin/bash
# S81 pre-test: fly NAME STICKMODE [PARAMS]; docker, wall timeout 600 s
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
R=indi_flight/results/stage5_s81_stick
P=""; [ -n "$3" ] && P="--params $3"
indi_project/docker/run.sh -n s81_$1 -t 600 -- python3 indi_flight/bench/run_scenario.py --scenario stick_zsine_o6 --controller $1 --model quad5in --seed 1 --speed 2 --stick-mode $2 $P --out $R/$1 > $R/$1.stdout.log 2>&1
echo "$1 docker_rc=$?" >> $R/status.txt
