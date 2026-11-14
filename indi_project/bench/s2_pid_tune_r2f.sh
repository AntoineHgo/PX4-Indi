#!/usr/bin/env bash
# v2 PID tuning round 2 on the FAC config (D-omega2): 16 candidates x 3 seeds centred on r1f c05 (J 0.925 vs
# defaults 0.966), same budget rule as v1 r2 and s2 r2. Waits for the frz control run (s2_queue_frz.sh) to end.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project
while pgrep -f 's2_queue_frz.sh|run_frz.sh' > /dev/null; do sleep 60; done
export SIM_VERSION=v2 IMU_RATE=1000 ERPM_DROP=0.01 VIB_ACC=1.0 VIB_GYR=0.05
export TUNE_REF_ROOT=$P/results/s2_tuning/ref_fac TUNE_REF_PARAMS=$P/bench/params/v2_fac.params TUNE_OUT_ROOT=$P/results/s2_tuning
exec timeout 14400 python3 indi_project/bench/tune.py --family pid --round-name r2f --n-candidates 16 --seeds 1 2 3 \
	--jobs 6 --sampler-seed 1 --span-factor 1.5 --base-params indi_project/bench/params/v2_fac.params \
	--center indi_project/bench/params/pid_r1f_c05.json
