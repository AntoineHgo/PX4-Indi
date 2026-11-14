#!/usr/bin/env bash
# v3 hover-effort check (session 46): hover seeds 2-5 (speed 1), pid_tuned vs v3 Tb 0 (= v2 inner loop) vs Tb 0.3 vs
# the two yaw survivors, v2 sim config. Answers whether the ~2x hover effort of seed 1 (results/v3_screen_yaw.md) is
# real (V' criterion 4: <= 1.5x pid_tuned). Resumable. Ends with V3_HOVER_DONE.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project
D=$P/results/v3_hover_effort/runs
V2=(--sim v2 --imu-rate 1000 --erpm-drop 0.01 --vib-acc 1.0 --vib-gyr 0.05)
declare -A PARAMS=([pid_tuned]=$P/results/s2_tuning/pid/r1f/c05/params [v3_tb0]=$P/bench/params/indi_v3_tb0.params
	[v3_tb0.3]=$P/bench/params/indi_v3_tb0.3.params [k2.733_c3.0]=$P/bench/params/indi_v3y_k2.733_c3.0.params
	[k4.0_c3.0]=$P/bench/params/indi_v3y_k4.0_c3.0.params)
run() {  # controller seed
	local out=$D/hover/$1/seed$2
	[ -f $out/metrics.json ] && return
	mkdir -p $out
	indi_project/docker/run.sh -n v3h-$1-$2 -t 900 -N python3 indi_project/bench/run_scenario.py --scenario hover \
		--controller $1 --seed $2 --speed 1 --out $out "${V2[@]}" --params ${PARAMS[$1]} > $out/runner.log 2>&1
	python3 indi_project/bench/metrics.py $out/flight.ulg > $out/metrics.log 2>&1
	echo "[v3h] $(date +%T) done hover $1 seed$2"
}
for seed in 2 3 4 5; do
	for c in pid_tuned v3_tb0 v3_tb0.3 k2.733_c3.0 k4.0_c3.0; do run $c $seed & done
	wait
done
echo V3_HOVER_DONE
