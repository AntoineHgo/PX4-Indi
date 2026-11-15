#!/usr/bin/env bash
# Stage-8 review findings 2 and 3: rebuild with the estimator accel-bias subtraction (F3, regression only: the gz IMU
# has no bias), then fly INDI POS with the identified MC_INDIP_DLY 0 (D-s8-delay): hover seed 1 (compare with
# results/s8e_qd_metric) and diag_z_multisine (lag check). v2 sim with vibration. Ends S8H_DONE.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project
R=$P/results/s8h_bias_dly0
mkdir -p $R
indi_project/docker/run.sh -n s8h-fmt -t 900 "make format" > $R/format.log 2>&1 || echo S8H_FORMAT_FAILED
git status --short src/ > $R/format_changes.txt
indi_project/docker/run.sh -n s8h-build -t 3000 "make px4_sitl_default" > $R/build.log 2>&1 || { echo S8H_BUILD_FAILED; exit 1; }
for sc in hover diag_z_multisine; do
	out=$R/${sc}_seed1
	mkdir -p $out
	indi_project/docker/run.sh -n s8h-fly -t 600 -N python3 indi_project/bench/run_scenario.py --scenario $sc \
		--controller indi_pos_v0 --seed 1 --speed 1 --out $out --sim v2 --imu-rate 1000 --erpm-drop 0.01 --vib-acc 1.0 \
		--vib-gyr 0.05 --params $P/bench/params/indi_pos_v0.params > $out/runner.log 2>&1
	python3 indi_project/bench/metrics.py $out/flight.ulg > $out/metrics.log 2>&1
	python3 indi_project/bench/ident_s8_delay.py $out/flight.ulg 0 > $out/delay.txt 2>&1
done
echo S8H_DONE
