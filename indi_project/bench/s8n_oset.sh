#!/usr/bin/env bash
# Stage-8 verdict batch on the frozen set O (bench/scenarios.md sec. 10): pid_tuned vs frozen indi_pos_v3, O1-O7,
# seeds 1-10, v2 sim, SENS_GNSS0_DELAY 0 (O-13 verdict pair, D-s8-gnss-delay). Validation: a watchdog abort is a
# reported failure, never re-flown (O-12), except host-suspend/estimator-glitch stalls per D-v2-refly.
# 4 flights at a time. Ends S8N_DONE, resumable by re-running (finished runs are skipped).
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project
D=$P/results/s8n_oset/runs
mkdir -p $D
V2=(--sim v2 --imu-rate 1000 --erpm-drop 0.01 --vib-acc 1.0 --vib-gyr 0.05 --gnss-delay 0)
PID=$P/results/s2_tuning/pid/r1f/c05/params
IPOS=$P/bench/params/indi_pos_v3.params
run() {  # entry controller params seed
	local out=$D/$1/$2/seed$4
	[ -f $out/metrics.json ] && return
	mkdir -p $out
	indi_project/docker/run.sh -n s8n-$1-$2-$4 -t 900 -N python3 indi_project/bench/run_scenario.py --scenario $1 \
		--controller $2 --seed $4 --speed 1 --out $out "${V2[@]}" --params $3 > $out/runner.log 2>&1
	python3 indi_project/bench/metrics.py $out/flight.ulg > $out/metrics.log 2>&1
	echo "[s8n] $(date +%T) done $1 $2 seed$4"
}
for seed in 1 2 3 4 5 6 7 8 9 10; do
	for e in o1_lemniscate o2_circle_z o3_lemniscate_gust o4_lemniscate_payload o5_zsine_com_shift o6_zsine_mass o7_lemniscate_tau2; do
		run $e pid_tuned $PID $seed & run $e indi_pos_v3 $IPOS $seed &
		[ $(jobs -r | wc -l) -ge 4 ] && wait -n
		[ $(jobs -r | wc -l) -ge 4 ] && wait -n
	done
done
wait
echo S8N_DONE
