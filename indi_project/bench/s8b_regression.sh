#!/usr/bin/env bash
# Stage-8 task B regression (plan/s8_impl_spec.md sec. 3): rebuild px4_sitl_default with mc_indi_pos_control built in,
# then fly the pid_tuned hover (MC_INDIP_EN 0, module not started) on seeds 1-2 with the pid_hover_mode idle setup, to
# compare with results/pid_hover_mode/runs/idle. Resumable. Ends with S8B_REGRESSION_DONE.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project
D=$P/results/s8b_regression/runs
V2=(--sim v2 --imu-rate 1000 --erpm-drop 0.01 --vib-acc 1.0 --vib-gyr 0.05)
PARAMS=$P/results/s2_tuning/pid/r1f/c05/params
mkdir -p $D
indi_project/docker/run.sh -n s8b-build -t 3000 'make px4_sitl_default' > $D/build.log 2>&1 || { echo S8B_BUILD_FAILED; exit 1; }
for seed in 1 2; do
	out=$D/seed$seed
	[ -f $out/metrics.json ] && continue
	mkdir -p $out
	indi_project/docker/run.sh -n s8b-$seed -t 600 -N python3 indi_project/bench/run_scenario.py --scenario hover \
		--controller pid_tuned --seed $seed --speed 1 --out $out "${V2[@]}" --params $PARAMS > $out/runner.log 2>&1
	python3 indi_project/bench/metrics.py $out/flight.ulg > $out/metrics.log 2>&1
	echo "[s8b] $(date +%T) done seed$seed"
done
echo S8B_REGRESSION_DONE
