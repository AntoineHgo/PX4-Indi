#!/usr/bin/env bash
# O-11 regression check: the frozen v1 INDI (v1 sim) and the v2 omega2 configuration (v2 sim) flown with the old
# placement (INDI inside mc_rate_control, measured torque in control_allocator) and the new module
# (build/px4_sitl_o11, mc_indi_rate_control). Same params files: run_scenario.py translates MC_RATE_CTL_TYPE and
# CA_R_W_MAX for the new binary. Old-binary v1 reference = results/s2_recheck_v1/runs/*/indi_frz (px4_sitl_default).
# Usage: SET=smoke|v1|v2old|v2new run.sh
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
D=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project/results/s2_o11_regress
NEW=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/build/px4_sitl_o11
OLD2=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/build/px4_sitl_omega2
V2=(--sim v2 --imu-rate 1000 --erpm-drop 0.01 --vib-acc 1.0 --vib-gyr 0.05)
run() {  # tag build params scenario seed speed [sim args...]
	local tag=$1 b=$2 p=$3 s=$4 seed=$5 sp=$6; shift 6
	local out=$D/runs/$tag/$s/seed$seed
	mkdir -p $out
	indi_project/docker/run.sh -n o11-$tag-$s-$seed -t 600 -N -e PX4_INDI_BUILD=$b python3 indi_project/bench/run_scenario.py \
		--scenario $s --controller indi_$tag --seed $seed --speed $sp --out $out "$@" --params $D/$p > $out/runner.log 2>&1
	python3 indi_project/bench/metrics.py $out/flight.ulg > $out/metrics.log 2>&1
	echo "[o11] $(date +%T) done $tag $s seed$seed"
}
set_runs() {  # tag build params [sim args...]: tuning set, seeds 1-3, 3 at a time
	local tag=$1 b=$2 p=$3; shift 3
	for seed in 1 2 3; do
		run $tag $b $p hover $seed 1 "$@" &
		run $tag $b $p step_roll $seed 4 "$@" &
		run $tag $b $p step_pitch $seed 4 "$@" &
		wait
		run $tag $b $p step_yaw $seed 4 "$@" &
		run $tag $b $p rate_step_roll $seed 4 "$@" &
		wait
	done
}
case ${SET:-} in
	smoke) run v1new $NEW indi_frz.params hover 1 1 ;;
	v1) set_runs v1new $NEW indi_frz.params ;;
	v2old) set_runs v2old $OLD2 indi_omega2.params "${V2[@]}" ;;
	v2new) set_runs v2new $NEW indi_omega2.params "${V2[@]}" ;;
esac
echo O11_${SET}_DONE
