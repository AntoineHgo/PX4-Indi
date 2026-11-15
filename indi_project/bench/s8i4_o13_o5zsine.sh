#!/usr/bin/env bash
# O-13 re-check of O5 moved to the vertical sine (com_shift injector valid only near level; circle runs kept in replaced_circle_*ms/). Flown once with pid_tuned (stock pipeline) on the v2 sim before the
# set is frozen in bench/scenarios.md sec. 10; an entry pid_tuned cannot fly is replaced. Feasibility only, no verdict.
# Ends S8I4_DONE.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project
D=$P/results/s8i_o13_precheck
mkdir -p $D

V2=(--sim v2 --imu-rate 1000 --erpm-drop 0.01 --vib-acc 1.0 --vib-gyr 0.05)
run() {  # entry
	local out=$D/$1/pid_tuned/seed1
	[ -f $out/metrics.json ] && return
	mkdir -p $out
	indi_project/docker/run.sh -n s8i4-$1 -t 900 -N python3 indi_project/bench/run_scenario.py --scenario $1 \
		--controller pid_tuned --seed 1 --speed 1 --out $out "${V2[@]}" \
		--params $P/results/s2_tuning/pid/r1f/c05/params > $out/runner.log 2>&1
	python3 indi_project/bench/metrics.py $out/flight.ulg > $out/metrics.log 2>&1
	echo "[s8i] $(date +%T) done $1"
}
run o5_zsine_com_shift
echo S8I4_DONE
