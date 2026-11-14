#!/usr/bin/env bash
# Stage-2 PID tuning check, round 2 (same budget as v1 pid r2), v2 nominal sim + D-notch, resumable.
# Optional argument: a candidate JSON to centre on (r1 best); without it the round centres on the defaults, as v1 r2.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project
export SIM_VERSION=v2 IMU_RATE=1000 ERPM_DROP=0.01 VIB_ACC=1.0 VIB_GYR=0.05
export TUNE_REF_ROOT=$P/results/s2_tuning/ref TUNE_REF_PARAMS=$P/bench/params/pid_dnf.params TUNE_OUT_ROOT=$P/results/s2_tuning
CENTER=()
[ -n "$1" ] && CENTER=(--center "$1")
exec timeout 14400 python3 indi_project/bench/tune.py --family pid --round-name r2 --n-candidates 16 --seeds 1 2 3 \
	--jobs 6 --sampler-seed 1 --span-factor 1.5 --base-params indi_project/bench/params/pid_dnf.params "${CENTER[@]}"
