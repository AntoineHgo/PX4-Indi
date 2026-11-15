#!/usr/bin/env bash
# Stage-8 arm C smoke (indi_pos_v3 with MC_INDIP_FF 0) on T5 seed 1: does the feedforward cause the 66 ms lead and the
# 2.4x effort seen in s8j_pos_v3_smoke? Seen entry only, not a verdict. Ends S8J2_DONE.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project
D=$P/results/s8j_pos_v3_smoke
mkdir -p $D
indi_project/docker/run.sh -n s8j2-build -t 3000 "make px4_sitl_default" > $D/build.log 2>&1 || { echo S8J_BUILD_FAILED; exit 1; }

V2=(--sim v2 --imu-rate 1000 --erpm-drop 0.01 --vib-acc 1.0 --vib-gyr 0.05)
run() {  # entry controller params
	local out=$D/$1/$2/seed1
	[ -f $out/metrics.json ] && return
	mkdir -p $out
	indi_project/docker/run.sh -n s8j2-$1-$2 -t 900 -N python3 indi_project/bench/run_scenario.py --scenario $1 \
		--controller $2 --seed 1 --speed 1 --out $out "${V2[@]}" --params $3 > $out/runner.log 2>&1
	python3 indi_project/bench/metrics.py $out/flight.ulg > $out/metrics.log 2>&1
	echo "[s8j] $(date +%T) done $1 $2"
}
run traj_lemniscate indi_pos_v3_ff0 $P/bench/params/indi_pos_v3_ff0.params &


wait
echo S8J2_DONE
