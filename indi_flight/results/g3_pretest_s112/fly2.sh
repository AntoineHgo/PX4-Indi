#!/bin/bash
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
R=indi_flight/results/g3_pretest_s112
true
indi_project/docker/run.sh -n g3pre_seed14 -t 1500 -- python3 $R/g3_one.py --seed 14 --n 20 --start 18 --base-params indi_flight/bench/params/quad5in_indi_g1.params --out-root $R/seed14 --timeout-s 1200
echo "seed14 docker_rc=$?"
