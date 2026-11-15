#!/usr/bin/env bash
# Stage-8 task B: first activation of the INDI POS external mode (hover seed 1, v2 sim, pid_tuned inner loops,
# MC_INDIP_EN 1, watchdog on). Diagnostic, not part of any verdict. Waits for the regression. Ends S8B_ACTIVATION_DONE.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project
until grep -q "S8B_REGRESSION_DONE\|S8B_BUILD_FAILED" $P/results/s8b_regression.log 2>/dev/null; do sleep 20; done
out=$P/results/s8b_activation/hover_seed1
mkdir -p $out
indi_project/docker/run.sh -n s8b-act -t 600 -N python3 indi_project/bench/run_scenario.py --scenario hover \
	--controller indi_pos_v0 --seed 1 --speed 1 --out $out --sim v2 --imu-rate 1000 --erpm-drop 0.01 --vib-acc 1.0 \
	--vib-gyr 0.05 --params $P/bench/params/indi_pos_v0.params > $out/runner.log 2>&1
python3 indi_project/bench/metrics.py $out/flight.ulg > $out/metrics.log 2>&1
indi_project/docker/run.sh -n s8b-chk -t 300 -N python3 indi_project/bench/s8b_activation_check.py $out/flight.ulg > $out/check.txt 2>&1
echo S8B_ACTIVATION_DONE
