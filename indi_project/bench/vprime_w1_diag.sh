#!/usr/bin/env bash
# Post-hoc W1 diagnostic (session 47, not part of the V' verdict): vp_loss1_06 seed 1 x 4 controllers with the
# watchdog off, to see whether any controller recovers from the altitude loss that aborted every V' W1 run.
# Resumable. Ends with VPRIME_W1_DIAG_DONE.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project
D=$P/results/vprime_w1_diag/runs
declare -A PARAMS=([pid_default]=$P/bench/params/v2_fac.params [pid_tuned]=$P/results/s2_tuning/pid/r1f/c05/params
	[indi_v2]=$P/bench/params/indi_v2_tuned.params [indi_v3]=$P/bench/params/indi_v3.params)
V2=(--sim v2 --imu-rate 1000 --erpm-drop 0.01 --vib-acc 1.0 --vib-gyr 0.05)
run() {  # controller
	local out=$D/vp_loss1_06/$1/seed1
	[ -f $out/metrics.json ] && return
	mkdir -p $out
	indi_project/docker/run.sh -n vpw1-$1 -t 900 -N python3 indi_project/bench/run_scenario.py --scenario vp_loss1_06 \
		--controller $1 --seed 1 --speed 1 --watchdog off --out $out "${V2[@]}" --params ${PARAMS[$1]} > $out/runner.log 2>&1
	python3 indi_project/bench/metrics.py $out/flight.ulg > $out/metrics.log 2>&1
	echo "[vpw1] $(date +%T) done $1"
}
for c in pid_default pid_tuned indi_v2 indi_v3; do run $c & done
wait
echo VPRIME_W1_DIAG_DONE
