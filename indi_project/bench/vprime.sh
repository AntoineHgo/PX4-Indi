#!/usr/bin/env bash
# v3 held-out set V' (bench/scenarios.md sec. 9, frozen): 5 entries x seeds x {pid_default, pid_tuned, indi_v2,
# indi_v3}. The four controllers of one (entry, seed) fly side by side, two entries at a time (8 containers), so every
# controller sees the same host load. Validation batch (O-12): a watchdog abort is a reported failure, never re-flown
# or dropped. Resumable: a run with a metrics.json is skipped. Ends with VPRIME_DONE.
# Usage: INDI_V3_PARAMS=<frozen v3 params file> [SEEDS="1 2"] vprime.sh
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project
D=$P/results/vprime/runs
[ -f "${INDI_V3_PARAMS:-}" ] || { echo "INDI_V3_PARAMS must name the frozen v3 INDI params file"; exit 1; }
declare -A PARAMS=([pid_default]=$P/bench/params/v2_fac.params [pid_tuned]=$P/results/s2_tuning/pid/r1f/c05/params
	[indi_v2]=$P/bench/params/indi_v2_tuned.params [indi_v3]=$INDI_V3_PARAMS)
V2=(--sim v2 --imu-rate 1000 --erpm-drop 0.01 --vib-acc 1.0 --vib-gyr 0.05)
# sec. 9: speed 1 for T8-pattern entries, 4 for attitude patterns
declare -A SPEED=([vp_loss1_06]=1 [vp_loss2_08]=1 [vp_gain03_att]=4 [vp_sag75_att]=4 [vp_tau2_loss2_att]=4)
run() {  # entry controller seed
	local out=$D/$1/$2/seed$3
	[ -f $out/metrics.json ] && return
	mkdir -p $out
	indi_project/docker/run.sh -n vp-$1-$2-$3 -t 900 -N python3 indi_project/bench/run_scenario.py --scenario $1 \
		--controller $2 --seed $3 --speed ${SPEED[$1]} --out $out "${V2[@]}" --params ${PARAMS[$2]} > $out/runner.log 2>&1
	python3 indi_project/bench/metrics.py $out/flight.ulg > $out/metrics.log 2>&1
	echo "[vp] $(date +%T) done $1 $2 seed$3"
}
quad() { for c in pid_default pid_tuned indi_v2 indi_v3; do run $1 $c $2 & done; }
for seed in ${SEEDS:-1 2 3 4 5 6 7 8 9 10}; do
	quad vp_loss1_06 $seed; quad vp_loss2_08 $seed; wait
	quad vp_gain03_att $seed; quad vp_sag75_att $seed; wait
	quad vp_tau2_loss2_att $seed; wait
done
echo VPRIME_DONE
