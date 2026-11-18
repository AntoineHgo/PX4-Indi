#!/bin/bash
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
R=indi_flight/results/g3_pretest_s112
indi_project/docker/run.sh -n g3pre_seed3b -t 1500 -- python3 $R/g3_one.py --seed 3 --n 20 --start 7 --base-params indi_flight/bench/params/quad5in_indi_g1.params --out-root $R/seed3b --timeout-s 1200
echo "seed3b docker_rc=$?"
