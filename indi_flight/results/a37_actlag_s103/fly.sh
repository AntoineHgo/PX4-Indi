#!/usr/bin/env bash
# A-37 closing test (S103): release-age windows of SIM_GZ_DLY_ACT in flight, d5 and d10, hover_long, serial. Run from repo root.
set -u
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi || exit 1
D=indi_flight/results/a37_actlag_s103
indi_project/docker/run.sh -n build -t 3600 'make px4_sitl_default' > $D/build.log 2>&1; echo "build exit=$?"
for a in 5 10; do
  indi_project/docker/run.sh -n a37_d$a -t 900 -- python3 indi_flight/bench/run_scenario.py --scenario hover_long --controller indi_m3a --seed 1 --speed 4 --model quad5in --rate-hz 800 --sim v2 --dly-act $a --dly-imu 0 --out $D/d$a > $D/d$a.stdout.log 2>&1
  echo "d$a exit=$?"
done
