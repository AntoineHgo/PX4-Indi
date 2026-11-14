#!/usr/bin/env bash
# v3 regression smoke (session 46): the v3 binary with MC_INDI_ACT_BLD 0 must fly like frozen indi_v2.
# hover seed 1 (speed 1) and step_roll seed 1 (speed 4), v2 sim config as s2_seen_v2.sh. Ends with V3_SMOKE_DONE.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project
D=$P/results/v3_smoke/runs
V2=(--sim v2 --imu-rate 1000 --erpm-drop 0.01 --vib-acc 1.0 --vib-gyr 0.05)
run() {  # entry speed
	local out=$D/$1/indi_v3_bld0/seed1
	[ -f $out/metrics.json ] && return
	mkdir -p $out
	indi_project/docker/run.sh -n v3s-$1 -t 900 -N python3 indi_project/bench/run_scenario.py --scenario $1 \
		--controller indi_v3_bld0 --seed 1 --speed $2 --out $out "${V2[@]}" --params $P/bench/params/indi_v3_bld0.params \
		> $out/runner.log 2>&1
	python3 indi_project/bench/metrics.py $out/flight.ulg > $out/metrics.log 2>&1
	echo "[v3s] $(date +%T) done $1"
}
run hover 1 &
run step_roll 4 &
wait
echo V3_SMOKE_DONE
