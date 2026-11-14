#!/usr/bin/env bash
# v2 held-out set V (bench/scenarios.md sec. 8, frozen): 14 entries x seeds x {pid_default, pid_tuned, indi_v2}.
# The three controllers of one (entry, seed) fly side by side, two pairs at a time (6 containers), so every
# controller sees the same host load (the O-11 regression showed load can move the metrics). Resumable: a run
# with a metrics.json is skipped. Usage: INDI_PARAMS=<v2 tuned INDI params file> [SEEDS="1 2"] s2_heldout_v2.sh
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project
D=$P/results/s2_heldout_v2/runs
[ -f "${INDI_PARAMS:-}" ] || { echo "INDI_PARAMS must name the v2 tuned INDI params file"; exit 1; }
declare -A PARAMS=([pid_default]=$P/bench/params/v2_fac.params [pid_tuned]=$P/results/s2_tuning/pid/r1f/c05/params
	[indi_v2]=$INDI_PARAMS)
V2=(--sim v2 --imu-rate 1000 --erpm-drop 0.01 --vib-acc 1.0 --vib-gyr 0.05)
# entry -> speed (D-speed: position scenarios and motor loss at 1, as in v1; attitude/rate patterns at 4)
declare -A SPEED=([v2_tau2_att]=4 [v2_tau2_rate]=4 [v2_asym_att]=4 [v2_asym_rate]=4 [v2_lat_att]=4 [v2_lat_rate]=4
	[v2_drop_att]=4 [v2_drop_rate]=4 [v2_vib3_hover]=1 [v2_vib3_att]=4 [v2_sag_att]=4 [gust_diag]=1 [com_shift]=1
	[motor_loss_0]=1)
ENTRIES=(v2_tau2_att v2_tau2_rate v2_asym_att v2_asym_rate v2_lat_att v2_lat_rate v2_drop_att v2_drop_rate
	v2_vib3_hover v2_vib3_att v2_sag_att gust_diag com_shift motor_loss_0)
run() {  # entry controller seed
	local out=$D/$1/$2/seed$3
	[ -f $out/metrics.json ] && return
	mkdir -p $out
	indi_project/docker/run.sh -n hv2-$1-$2-$3 -t 900 -N python3 indi_project/bench/run_scenario.py --scenario $1 \
		--controller $2 --seed $3 --speed ${SPEED[$1]} --out $out "${V2[@]}" --params ${PARAMS[$2]} > $out/runner.log 2>&1
	python3 indi_project/bench/metrics.py $out/flight.ulg > $out/metrics.log 2>&1
	echo "[hv2] $(date +%T) done $1 $2 seed$3"
}
triple() { for c in pid_default pid_tuned indi_v2; do run $1 $c $2 & done; }
for seed in ${SEEDS:-1 2 3 4 5 6 7 8 9 10}; do
	for ((i = 0; i < ${#ENTRIES[@]}; i += 2)); do
		triple ${ENTRIES[i]} $seed
		triple ${ENTRIES[i + 1]} $seed
		wait
	done
done
echo HELDOUT_V2_DONE
