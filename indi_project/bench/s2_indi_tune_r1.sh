#!/usr/bin/env bash
# Stage-2 INDI v2 tuning, round 1 (same budget as v2 PID r1f: 24 candidates x 2 seeds), v2 sim, FAC config, resumable.
# Start point bench/params/indi_v2_start.params: G1 identified on 3 seeds (results/s2_g1_v2.md), ACT_TC and ERPM_DLY
# identified (O-3, D-erpmdly) and fixed; centre = frozen v1 gains. Varies gains and YAW_CUT only (D-v2indi-tune).
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project
export SIM_VERSION=v2 IMU_RATE=1000 ERPM_DROP=0.01 VIB_ACC=1.0 VIB_GYR=0.05
export TUNE_REF_ROOT=$P/results/s2_tuning/ref_fac TUNE_REF_PARAMS=$P/bench/params/v2_fac.params TUNE_OUT_ROOT=$P/results/s2_tuning
exec timeout 14400 python3 indi_project/bench/tune.py --family indi --round-name r1 --n-candidates 24 --seeds 1 2 \
	--jobs 6 --sampler-seed 0 --span-factor 2.0 --base-params indi_project/bench/params/indi_v2_start.params \
	--vary MC_INDI_K_R MC_INDI_K_P MC_INDI_K_Y MC_INDI_YAW_CUT MC_ROLL_P MC_PITCH_P MC_YAW_P "$@"
