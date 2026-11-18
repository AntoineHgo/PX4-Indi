#!/bin/bash
# S83 stick re-fly with sim-time grid pacing (S82 Sim.sp_grid), answering second key DEVIATION (33 Hz rows).
# usage: bash fly.sh NAME STICKMODE [PARAMS] (NAME is the run label; the stack comes from PARAMS); docker, wall timeout 600 s
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
R=indi_flight/results/stage5_s83_stick
P=""; [ -n "$3" ] && P="--params $3"
indi_project/docker/run.sh -n s83_$1 -t 600 -- python3 indi_flight/bench/run_scenario.py --scenario stick_zsine_o6 --controller $1 --model quad5in --seed 1 --speed 2 --stick-mode $2 $P --out $R/$1 > $R/$1.stdout.log 2>&1
echo "$1 docker_rc=$?" >> $R/status.txt
