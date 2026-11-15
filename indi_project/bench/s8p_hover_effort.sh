#!/usr/bin/env bash
# Stage-8 criterion 4 (hover effort, scenarios.md sec. 10) on 10 seeds instead of the 2 smoke seeds, because the
# pid_tuned hover effort spreads per flight (D-hover-spread, D-s8-hover10): T1 hover seeds 3-10 for the verdict pair,
# same v2 configuration and SENS_GNSS0_DELAY 0 as set O, written next to the s8m seeds 1-2. Waits for S8N_DONE so
# the set-O batch keeps its 4-flight load. Ends S8P_DONE, resumable by re-running (finished runs are skipped).
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project
D=$P/results/s8m_smoke_gnss0
V2=(--sim v2 --imu-rate 1000 --erpm-drop 0.01 --vib-acc 1.0 --vib-gyr 0.05 --gnss-delay 0)
PID=$P/results/s2_tuning/pid/r1f/c05/params
IPOS=$P/bench/params/indi_pos_v3.params
until grep -q S8N_DONE $P/results/s8n_oset.log 2>/dev/null; do sleep 60; done
run() {  # entry controller params seed
	local out=$D/$1/$2/seed$4
	[ -f $out/metrics.json ] && return
	mkdir -p $out
	indi_project/docker/run.sh -n s8p-$1-$2-$4 -t 900 -N python3 indi_project/bench/run_scenario.py --scenario $1 \
		--controller $2 --seed $4 --speed 1 --out $out "${V2[@]}" --params $3 > $out/runner.log 2>&1
	python3 indi_project/bench/metrics.py $out/flight.ulg > $out/metrics.log 2>&1
	echo "[s8p] $(date +%T) done $1 $2 seed$4"
}
for seed in 3 5 7 9; do
	run hover pid_tuned $PID $seed & run hover indi_pos_v3 $IPOS $seed &
	run hover pid_tuned $PID $((seed + 1)) & run hover indi_pos_v3 $IPOS $((seed + 1)) & wait
done
echo S8P_DONE
