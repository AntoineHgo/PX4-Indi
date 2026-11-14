#!/usr/bin/env bash
# Post-acceptance re-checks of the FROZEN v1 INDI (O-3, O-4), v1 sim config (stock gz_x500, no v2 env, FAC 0).
# Variants: indi_tcup (MC_INDI_ACT_TC = identified tau up 12.5 ms), indi_tcdn (tau down 25 ms; the library has one
# tc), indi_g2 (frozen + MC_INDI_G2_Y 0.16, D-g2sim). Frozen = r4f/c00 (results/act_tc_sweep_s17/indi_act1.0.params).
# Tuning set (hover x1, steps/rate x4, seeds 1-3) and H5 (mismatch_combined_att/_rate x4, seeds 1-10), as v1.
# Resumable only per batch: re-running repeats finished runs. Requires px4_sitl_default rebuilt after s31.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
D=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project/results/s2_recheck_v1
for v in tcup tcdn g2; do
  common=(CONTROLLERS=indi_$v PARAMS_FILE=$D/indi_$v.params RESULTS_DIR=$D/runs TIMEOUT=600 NAME_TAG=rc$v)
  env "${common[@]}" SCENARIOS=hover SEEDS="1 2 3" SPEEDS=1 JOBS=3 indi_project/bench/run_batch.sh
  env "${common[@]}" SCENARIOS="step_roll step_pitch step_yaw rate_step_roll" SEEDS="1 2 3" SPEEDS=4 JOBS=6 \
    indi_project/bench/run_batch.sh
  env "${common[@]}" SCENARIOS="mismatch_combined_att mismatch_combined_rate" SEEDS="1 2 3 4 5 6 7 8 9 10" SPEEDS=4 \
    JOBS=6 indi_project/bench/run_batch.sh
done
echo RECHECK_DONE
