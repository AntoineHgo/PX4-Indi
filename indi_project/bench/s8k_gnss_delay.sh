#!/usr/bin/env bash
# D-s8-gnss-delay check: T5 seed 1, pid_tuned and indi_pos_v3 (jerk LPF), SENS_GNSS0_DELAY 0 (gz GNSS has no latency).
# Expect the EKF-vs-ground-truth position lag (gt_lag.py) to drop from ~110 ms to ~0. Uses the binary built by s8j3. Ends S8K_DONE.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project
D=$P/results/s8k_gnss_delay

V2=(--sim v2 --imu-rate 1000 --erpm-drop 0.01 --vib-acc 1.0 --vib-gyr 0.05 --gnss-delay 0)
run() {  # entry controller params
	local out=$D/$1/$2/seed1
	[ -f $out/metrics.json ] && return
	mkdir -p $out
	indi_project/docker/run.sh -n s8k-$1-$2 -t 900 -N python3 indi_project/bench/run_scenario.py --scenario $1 \
		--controller $2 --seed 1 --speed 1 --out $out "${V2[@]}" --params $3 > $out/runner.log 2>&1
	python3 indi_project/bench/metrics.py $out/flight.ulg > $out/metrics.log 2>&1
	python3 indi_project/bench/gt_lag.py $out/flight.ulg > $out/gt_lag.log 2>&1
	echo "[s8k] $(date +%T) done $1 $2"
}
run traj_lemniscate pid_tuned $P/results/s2_tuning/pid/r1f/c05/params &
run traj_lemniscate indi_pos_v3_jlpf $P/bench/params/indi_pos_v3.params &
wait
echo S8K_DONE
