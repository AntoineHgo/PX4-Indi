#!/usr/bin/env bash
# O-12 stage-1 screen before freezing indi_pos_v3, seen entries only, SENS_GNSS0_DELAY 0. (a) Hover-effort attribution:
# indi_v3 rate loop under the stock outer loop, T1 hover seeds 1-2 (compare s8m indi_pos_v3 / pid_tuned).
# (b) MC_INDIP_LPF_CUT 5 Hz (vs 10): T1 hover seeds 1-2, T5 seed 1, H1 seed 1. Ends S8O_DONE, resumable.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project
D=$P/results/s8m_smoke_gnss0
V2=(--sim v2 --imu-rate 1000 --erpm-drop 0.01 --vib-acc 1.0 --vib-gyr 0.05 --gnss-delay 0)
run() {  # entry controller params seed
	local out=$D/$1/$2/seed$4
	[ -f $out/metrics.json ] && return
	mkdir -p $out
	indi_project/docker/run.sh -n s8o-$1-$2-$4 -t 900 -N python3 indi_project/bench/run_scenario.py --scenario $1 \
		--controller $2 --seed $4 --speed 1 --out $out "${V2[@]}" --params $3 > $out/runner.log 2>&1
	python3 indi_project/bench/metrics.py $out/flight.ulg > $out/metrics.log 2>&1
	echo "[s8o] $(date +%T) done $1 $2 seed$4"
}
L5=$P/bench/params/indi_pos_v3_lpf5.params
run hover indi_v3 $P/bench/params/indi_v3.params 1 & run hover indi_v3 $P/bench/params/indi_v3.params 2 &
run hover indi_pos_v3_lpf5 $L5 1 & run hover indi_pos_v3_lpf5 $L5 2 & wait
run traj_lemniscate indi_pos_v3_lpf5 $L5 1 & run traj_circle_fast indi_pos_v3_lpf5 $L5 1 & wait
echo S8O_DONE
