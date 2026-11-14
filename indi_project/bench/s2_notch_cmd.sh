#!/usr/bin/env bash
# Session 29 D-notch check: PID defaults + ESC-rpm dynamic notch on v2 nominal.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
export SIM_VERSION=v2 IMU_RATE=1000 ERPM_DROP=0.01 VIB_ACC=1.0 VIB_GYR=0.05 TIMEOUT=600
export RESULTS_DIR=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project/results/s2_notch
CONTROLLERS=pid_dnf SCENARIOS=hover SEEDS="1 2 3" SPEEDS=1 JOBS=3 NAME_TAG=nh indi_project/bench/run_batch.sh > indi_project/results/s2_notch_hover.log 2>&1 &
CONTROLLERS=pid_dnf SCENARIOS="step_roll rate_step_roll" SEEDS="1 2 3" SPEEDS=4 JOBS=3 NAME_TAG=ns indi_project/bench/run_batch.sh > indi_project/results/s2_notch_steps.log 2>&1
wait
