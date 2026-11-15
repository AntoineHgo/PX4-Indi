#!/usr/bin/env bash
# O-13 pre-check of the stage-8 set O1-O7: each entry flown once with pid_tuned (stock pipeline) on the v2 sim before the
# set is frozen in bench/scenarios.md sec. 10; an entry pid_tuned cannot fly is replaced. Feasibility only, no verdict.
# Waits for the s8h flights to end first. Ends S8I_DONE.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project
D=$P/results/s8i_o13_precheck
mkdir -p $D
until grep -q "S8H_DONE\|S8H_BUILD_FAILED" $P/results/s8h_bias_dly0.log 2>/dev/null; do sleep 10; done
V2=(--sim v2 --imu-rate 1000 --erpm-drop 0.01 --vib-acc 1.0 --vib-gyr 0.05)
run() {  # entry
	local out=$D/$1/pid_tuned/seed1
	[ -f $out/metrics.json ] && return
	mkdir -p $out
	indi_project/docker/run.sh -n s8i-$1 -t 900 -N python3 indi_project/bench/run_scenario.py --scenario $1 \
		--controller pid_tuned --seed 1 --speed 1 --out $out "${V2[@]}" \
		--params $P/results/s2_tuning/pid/r1f/c05/params > $out/runner.log 2>&1
	python3 indi_project/bench/metrics.py $out/flight.ulg > $out/metrics.log 2>&1
	echo "[s8i] $(date +%T) done $1"
}
run o1_lemniscate & run o2_circle_z & run o3_lemniscate_gust & run o4_lemniscate_payload & wait
run o5_circle_com_shift & run o6_zsine_mass & run o7_lemniscate_tau2 & wait
echo S8I_DONE
