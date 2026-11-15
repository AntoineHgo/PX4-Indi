#!/usr/bin/env bash
# Causal test of the hover-effort note (results/s2_hover_effort_cause.md sec. 4, session 48): hover seeds 1-3, speed 1,
# v2 sim config, indi_v2 vs indi_v2 with the measured torque disabled (MC_INDI_W_MAX 0, model state) vs pid_tuned.
# Post-hoc diagnostic, not part of any verdict. Resumable. Ends with HOVER_CAUSE_DONE.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project
D=$P/results/hover_cause/runs
V2=(--sim v2 --imu-rate 1000 --erpm-drop 0.01 --vib-acc 1.0 --vib-gyr 0.05)
declare -A PARAMS=([pid_tuned]=$P/results/s2_tuning/pid/r1f/c05/params [indi_v2]=$P/bench/params/indi_v2_tuned.params
	[indi_v2_wmax0]=$P/bench/params/indi_v2_wmax0.params)
run() {  # controller seed
	local out=$D/hover/$1/seed$2
	[ -f $out/metrics.json ] && return
	mkdir -p $out
	indi_project/docker/run.sh -n hc-$1-$2 -t 900 -N python3 indi_project/bench/run_scenario.py --scenario hover \
		--controller $1 --seed $2 --speed 1 --out $out "${V2[@]}" --params ${PARAMS[$1]} > $out/runner.log 2>&1
	python3 indi_project/bench/metrics.py $out/flight.ulg > $out/metrics.log 2>&1
	echo "[hc] $(date +%T) done hover $1 seed$2"
}
for seed in 1 2 3; do
	for c in pid_tuned indi_v2 indi_v2_wmax0; do run $c $seed & done
	wait
done
echo HOVER_CAUSE_DONE
