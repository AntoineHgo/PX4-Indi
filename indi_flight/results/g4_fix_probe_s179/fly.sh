#!/usr/bin/env bash
cd "$(dirname "$0")/../../.." || exit 1
R=indi_flight/results/g4_fix_probe_s179
s=$1; n=$2
common="--controller indi --model quad5in --seed $s --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 --scenario traj_lemniscate --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0"
timeout 1300 indi_project/docker/run.sh -n $n -t 1300 -- python3 indi_flight/bench/run_scenario.py $common --params $R/f1_params.params --out $R/f1_lpf5_s$s > $R/f1_s$s.log 2>&1
echo "rc $?" > $R/f1_s$s.done
