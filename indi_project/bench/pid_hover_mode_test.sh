#!/usr/bin/env bash
# pid_tuned 2-4 Hz hover mode (owner note 2026-11-15, results/pid_hover_mode.md hypothesis 1 and 3): hover seeds 1-2,
# each flown twice, one flight at a time, first on an otherwise idle host, then with 16 busy-loop processes
# saturating the CPU. Post-hoc diagnostic, not part of any verdict. Resumable. Ends with PID_HOVER_MODE_DONE.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project
D=$P/results/pid_hover_mode/runs
V2=(--sim v2 --imu-rate 1000 --erpm-drop 0.01 --vib-acc 1.0 --vib-gyr 0.05)
PARAMS=$P/results/s2_tuning/pid/r1f/c05/params
run() {  # condition seed repeat
	local out=$D/$1/seed$2_r$3
	[ -f $out/metrics.json ] && return
	mkdir -p $out
	uptime > $out/load_before.txt
	indi_project/docker/run.sh -n phm-$1-$2-$3 -t 600 -N python3 indi_project/bench/run_scenario.py --scenario hover \
		--controller pid_tuned --seed $2 --speed 1 --out $out "${V2[@]}" --params $PARAMS > $out/runner.log 2>&1
	uptime > $out/load_after.txt
	python3 indi_project/bench/metrics.py $out/flight.ulg > $out/metrics.log 2>&1
	echo "[phm] $(date +%T) done $1 seed$2 r$3"
}
for r in 1 2; do for seed in 1 2; do run idle $seed $r; done; done
PIDS=()
for i in $(seq 16); do timeout 1200 python3 -c 'while True: pass' & PIDS+=($!); done
for r in 1 2; do for seed in 1 2; do run load $seed $r; done; done
kill "${PIDS[@]}" 2>/dev/null
echo PID_HOVER_MODE_DONE
