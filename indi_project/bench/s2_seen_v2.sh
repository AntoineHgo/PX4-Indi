#!/usr/bin/env bash
# v2 seen set (O-7, bench/scenarios.md sec. 8): H1, H4-H6, T1-T7 and mismatch_inertia re-flown on the v2
# configuration, labelled "seen" (H2/H3/T8 are V7-V9 in s2_heldout_v2.sh). Same layout as s2_heldout_v2.sh:
# 14 entries x seeds x {pid_default, pid_tuned, indi_v2}.
# The three controllers of one (entry, seed) fly side by side, two pairs at a time (6 containers), so every
# controller sees the same host load (the O-11 regression showed load can move the metrics). Resumable: a run
# with a metrics.json is skipped. Waits for HELDOUT_V2_DONE in the V log so the two batches never share the host.
# Usage: INDI_PARAMS=<v2 tuned INDI params file> [SEEDS="1 2"] s2_seen_v2.sh
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project
D=$P/results/s2_seen_v2/runs
[ -f "${INDI_PARAMS:-}" ] || { echo "INDI_PARAMS must name the v2 tuned INDI params file"; exit 1; }
declare -A PARAMS=([pid_default]=$P/bench/params/v2_fac.params [pid_tuned]=$P/results/s2_tuning/pid/r1f/c05/params
	[indi_v2]=$INDI_PARAMS)
V2=(--sim v2 --imu-rate 1000 --erpm-drop 0.01 --vib-acc 1.0 --vib-gyr 0.05)
# entry -> speed (D-speed: position scenarios and motor loss at 1, as in v1; attitude/rate patterns at 4)
declare -A SPEED=([traj_circle_fast]=1 [motor_loss_2]=1 [mismatch_combined_att]=4 [mismatch_combined_rate]=4
	[step_diag]=4 [traj_lemniscate]=1 [gust_x]=1 [payload_add]=1 [hover]=1 [step_roll]=4 [step_pitch]=4 [step_yaw]=4
	[rate_step_roll]=4 [mismatch_inertia]=4)
ENTRIES=(traj_circle_fast motor_loss_2 mismatch_combined_att mismatch_combined_rate step_diag traj_lemniscate gust_x
	payload_add hover step_roll step_pitch step_yaw rate_step_roll mismatch_inertia)
until grep -q HELDOUT_V2_DONE $P/results/s2_heldout_v2/run.log 2>/dev/null; do sleep 60; done
run() {  # entry controller seed
	local out=$D/$1/$2/seed$3
	[ -f $out/metrics.json ] && return
	mkdir -p $out
	indi_project/docker/run.sh -n sv2-$1-$2-$3 -t 900 -N python3 indi_project/bench/run_scenario.py --scenario $1 \
		--controller $2 --seed $3 --speed ${SPEED[$1]} --out $out "${V2[@]}" --params ${PARAMS[$2]} > $out/runner.log 2>&1
	python3 indi_project/bench/metrics.py $out/flight.ulg > $out/metrics.log 2>&1
	echo "[sv2] $(date +%T) done $1 $2 seed$3"
}
triple() { for c in pid_default pid_tuned indi_v2; do run $1 $c $2 & done; }
for seed in ${SEEDS:-1 2 3 4 5 6 7 8 9 10}; do
	for ((i = 0; i < ${#ENTRIES[@]}; i += 2)); do
		triple ${ENTRIES[i]} $seed
		triple ${ENTRIES[i + 1]} $seed
		wait
	done
done
echo SEEN_V2_DONE
