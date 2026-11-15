#!/usr/bin/env bash
# Stage-8 review finding 6: hover with q_d logged in indi_pos_status, attitude metric from it.
# (every sensor_combined sample averaged over the control cycle). Diagnostic, not part of any verdict.
# Compare with results/s8b_activation/hover_seed1 (latest sample, 5.47 deg) and hover_seed1_vib0 (0.33 deg).
# Ends S8E_ACCEL_DONE.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project
out=$P/results/s8e_qd_metric/hover_seed1
mkdir -p $out
indi_project/docker/run.sh -n s8e-build -t 3000 "make px4_sitl_default" > $P/results/s8e_qd_metric/build.log 2>&1 || { echo S8E_BUILD_FAILED; exit 1; }
indi_project/docker/run.sh -n s8e-fly -t 600 -N python3 indi_project/bench/run_scenario.py --scenario hover \
	--controller indi_pos_v0 --seed 1 --speed 1 --out $out --sim v2 --imu-rate 1000 --erpm-drop 0.01 --vib-acc 1.0 \
	--vib-gyr 0.05 --params $P/bench/params/indi_pos_v0.params > $out/runner.log 2>&1
python3 indi_project/bench/metrics.py $out/flight.ulg > $out/metrics.log 2>&1
indi_project/docker/run.sh -n s8e-chk -t 300 -N python3 indi_project/bench/s8b_activation_check.py $out/flight.ulg > $out/check.txt 2>&1
echo S8E_ACCEL_DONE
