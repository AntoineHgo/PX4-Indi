#!/usr/bin/env bash
# v3 stage-1 screening (session 46, O-12, D-outer-check): MC_INDI_ACT_BLD Tb in {0, 0.1, 0.3, 1.0} on indi_v2 with
# tuned PID's outer gains, vs pid_tuned, seed 1, on motor_loss_0 (T8, speed 1), mismatch_combined_rate and step_roll
# (speed 4); v2 sim config as s2_seen_v2.sh. One entry across all five configs at a time. Watchdog on (default).
# Resumable. Ends with V3_SCREEN_DONE.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project
D=$P/results/v3_screen/runs
declare -A PARAMS=([pid_tuned]=$P/results/s2_tuning/pid/r1f/c05/params [v3_tb0]=$P/bench/params/indi_v3_tb0.params
	[v3_tb0.1]=$P/bench/params/indi_v3_tb0.1.params [v3_tb0.3]=$P/bench/params/indi_v3_tb0.3.params
	[v3_tb1.0]=$P/bench/params/indi_v3_tb1.0.params)
declare -A SPEED=([motor_loss_0]=1 [mismatch_combined_rate]=4 [step_roll]=4)
V2=(--sim v2 --imu-rate 1000 --erpm-drop 0.01 --vib-acc 1.0 --vib-gyr 0.05)
run() {  # entry controller seed
	local out=$D/$1/$2/seed$3
	[ -f $out/metrics.json ] && return
	mkdir -p $out
	indi_project/docker/run.sh -n v3sc-$1-$2-$3 -t 900 -N python3 indi_project/bench/run_scenario.py --scenario $1 \
		--controller $2 --seed $3 --speed ${SPEED[$1]} --out $out "${V2[@]}" --params ${PARAMS[$2]} > $out/runner.log 2>&1
	python3 indi_project/bench/metrics.py $out/flight.ulg > $out/metrics.log 2>&1
	echo "[v3sc] $(date +%T) done $1 $2 seed$3"
}
for seed in ${SEEDS:-1}; do
	for e in motor_loss_0 mismatch_combined_rate step_roll; do
		for c in pid_tuned v3_tb0 v3_tb0.1 v3_tb0.3 v3_tb1.0; do run $e $c $seed & done
		wait
	done
done
echo V3_SCREEN_DONE
