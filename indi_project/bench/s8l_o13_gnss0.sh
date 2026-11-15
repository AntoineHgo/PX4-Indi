#!/usr/bin/env bash
# O-13 pre-check of the frozen set O1-O7 re-flown with SENS_GNSS0_DELAY 0 (D-s8-gnss-delay): pid_tuned, seed 1, v2 sim.
# Feasibility only, no verdict. Waits for the s8k check. Ends S8L_DONE, resumable by re-running.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project
D=$P/results/s8l_o13_gnss0
mkdir -p $D
until grep -q "S8K_DONE" $P/results/s8k_gnss_delay/s8k.log 2>/dev/null; do sleep 10; done
V2=(--sim v2 --imu-rate 1000 --erpm-drop 0.01 --vib-acc 1.0 --vib-gyr 0.05 --gnss-delay 0)
run() {  # entry
	local out=$D/$1/pid_tuned/seed1
	[ -f $out/metrics.json ] && return
	mkdir -p $out
	indi_project/docker/run.sh -n s8l-$1 -t 900 -N python3 indi_project/bench/run_scenario.py --scenario $1 \
		--controller pid_tuned --seed 1 --speed 1 --out $out "${V2[@]}" \
		--params $P/results/s2_tuning/pid/r1f/c05/params > $out/runner.log 2>&1
	python3 indi_project/bench/metrics.py $out/flight.ulg > $out/metrics.log 2>&1
	python3 indi_project/bench/gt_lag.py $out/flight.ulg > $out/gt_lag.log 2>&1
	echo "[s8l] $(date +%T) done $1"
}
run o1_lemniscate & run o2_circle_z & run o3_lemniscate_gust & run o4_lemniscate_payload & wait
run o5_zsine_com_shift & run o6_zsine_mass & run o7_lemniscate_tau2 & wait
echo S8L_DONE
