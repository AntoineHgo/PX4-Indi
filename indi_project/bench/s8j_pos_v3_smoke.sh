#!/usr/bin/env bash
# Stage-8 smoke of arm D (indi_pos_v3: INDI POS on the frozen indi_v3 rate loop) on seen entries only: T5 lemniscate and
# T1 hover, seed 1, with pid_tuned on T5 alongside for reference. Not a verdict (set O is never flown for tuning).
# Ends S8J_DONE.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project
D=$P/results/s8j_pos_v3_smoke
mkdir -p $D
indi_project/docker/run.sh -n s8j-build -t 3000 "make px4_sitl_default" > $D/build.log 2>&1 || { echo S8J_BUILD_FAILED; exit 1; }

V2=(--sim v2 --imu-rate 1000 --erpm-drop 0.01 --vib-acc 1.0 --vib-gyr 0.05)
run() {  # entry controller params
	local out=$D/$1/$2/seed1
	[ -f $out/metrics.json ] && return
	mkdir -p $out
	indi_project/docker/run.sh -n s8j-$1-$2 -t 900 -N python3 indi_project/bench/run_scenario.py --scenario $1 \
		--controller $2 --seed 1 --speed 1 --out $out "${V2[@]}" --params $3 > $out/runner.log 2>&1
	python3 indi_project/bench/metrics.py $out/flight.ulg > $out/metrics.log 2>&1
	echo "[s8j] $(date +%T) done $1 $2"
}
run traj_lemniscate indi_pos_v3 $P/bench/params/indi_pos_v3.params &
run hover indi_pos_v3 $P/bench/params/indi_pos_v3.params &
run traj_lemniscate pid_tuned $P/results/s2_tuning/pid/r1f/c05/params &
wait
echo S8J_DONE
