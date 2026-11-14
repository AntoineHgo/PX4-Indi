#!/usr/bin/env bash
# Post-acceptance ACT_TC robustness sweep (D-actsweep): frozen INDI, MC_INDI_ACT_TC x f on the stock gz_x500 plant,
# so plant/model motor time-constant ratio = 1/f. step_roll, speed 4, seeds 1-3.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
for f in 0.33 0.5 0.67 1.0 1.5 2.0 3.0; do
  SCENARIOS=step_roll CONTROLLERS=indi_act$f SEEDS="1 2 3" SPEEDS=4 TIMEOUT=600 JOBS=3 NAME_TAG=act$f \
    PARAMS_FILE=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project/results/act_tc_sweep_s17/indi_act$f.params indi_project/bench/run_batch.sh
done
echo SWEEP_DONE
