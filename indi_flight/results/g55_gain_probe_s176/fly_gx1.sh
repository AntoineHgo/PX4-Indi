#!/usr/bin/env bash
# S176 G5.5 gain probe: freeze fly.sh command for o1 seed 1 with params_gx1.params = freeze params + MPC_XY_P 1.9, MPC_XY_VEL_P_ACC 3.6. Repo root.
D=indi_flight/results/g55_gain_probe_s176
timeout 1000 indi_project/docker/run.sh -n s176gx1 -t 900 -- python3 indi_flight/bench/run_scenario.py --controller indi \
  --model quad5in --seed 1 --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 \
  --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0 \
  --params $D/params_gx1.params --scenario o1_lemniscate --out $D/indi_o1_s1_gx1 > $D/indi_o1_s1_gx1.stdout.log 2>&1
echo "rc=$?"
