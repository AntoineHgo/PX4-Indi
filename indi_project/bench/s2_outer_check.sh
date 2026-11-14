#!/usr/bin/env bash
# Diagnostic (session 46): is INDI v2's nominal step deficit the outer attitude-loop tuning?
# indi_v2 (frozen) vs indi_v2_pidouter (same, with tuned PID's MC_ROLL_P/PITCH_P/YAW_P) vs pid_tuned,
# nominal step/rate entries, seeds 1-3, v2 sim config identical to s2_seen_v2.sh. Same-(entry, seed) triples
# fly side by side, two triples at a time. Resumable. Ends with OUTER_CHECK_DONE.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project
D=$P/results/s2_outer_check/runs
declare -A PARAMS=([pid_tuned]=$P/results/s2_tuning/pid/r1f/c05/params [indi_v2]=$P/bench/params/indi_v2_tuned.params
	[indi_v2_pidouter]=$P/bench/params/indi_v2_pidouter.params)
V2=(--sim v2 --imu-rate 1000 --erpm-drop 0.01 --vib-acc 1.0 --vib-gyr 0.05)
ENTRIES=(step_roll step_pitch step_yaw step_diag rate_step_roll)
run() {  # entry controller seed
	local out=$D/$1/$2/seed$3
	[ -f $out/metrics.json ] && return
	mkdir -p $out
	indi_project/docker/run.sh -n oc-$1-$2-$3 -t 900 -N python3 indi_project/bench/run_scenario.py --scenario $1 \
		--controller $2 --seed $3 --speed 4 --out $out "${V2[@]}" --params ${PARAMS[$2]} > $out/runner.log 2>&1
	python3 indi_project/bench/metrics.py $out/flight.ulg > $out/metrics.log 2>&1
	echo "[oc] $(date +%T) done $1 $2 seed$3"
}
triple() { for c in pid_tuned indi_v2 indi_v2_pidouter; do run $1 $c $2 & done; }
for seed in ${SEEDS:-1 2 3}; do
	for ((i = 0; i < 5; i += 2)); do
		triple ${ENTRIES[i]} $seed
		[ $((i + 1)) -lt 5 ] && triple ${ENTRIES[i + 1]} $seed
		wait
	done
done
echo OUTER_CHECK_DONE
