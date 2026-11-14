#!/usr/bin/env bash
# Stage-2 PID tuning check, round 1 (same budget as v1 pid r1), v2 nominal sim + D-notch, resumable.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project
export SIM_VERSION=v2 IMU_RATE=1000 ERPM_DROP=0.01 VIB_ACC=1.0 VIB_GYR=0.05
export TUNE_REF_ROOT=$P/results/s2_tuning/ref TUNE_REF_PARAMS=$P/bench/params/pid_dnf.params TUNE_OUT_ROOT=$P/results/s2_tuning
exec timeout 14400 python3 indi_project/bench/tune.py --family pid --round-name r1 --n-candidates 24 --seeds 1 2 \
	--jobs 6 --sampler-seed 0 --span-factor 2.0 --base-params indi_project/bench/params/pid_dnf.params
