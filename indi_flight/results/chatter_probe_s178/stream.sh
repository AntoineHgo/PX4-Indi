#!/usr/bin/env bash
cd "$(dirname "$0")/../../.." || exit 1
R=indi_flight/results/chatter_probe_s178
common="--controller indi --model quad5in --seed 1 --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 --scenario traj_lemniscate --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0"
timeout 1300 indi_project/docker/run.sh -n s178p1 -t 1300 -- python3 indi_flight/bench/run_scenario.py $common --params $R/p1_params.params --out $R/p1_vel_lp8 > $R/p1.log 2>&1
timeout 1300 indi_project/docker/run.sh -n s178p2 -t 1300 -e INDI_SP_PERIOD=0.01 -- python3 indi_flight/bench/run_scenario.py $common --params indi_flight/results/g5_freeze_s157/params.params --out $R/p2_sp10ms > $R/p2.log 2>&1
echo done > $R/STREAM_END
