#!/usr/bin/env bash
# v3 yaw stage-2 screening (session 47, O-12): the yaw stage-1 base (K_Y 2.733, cut 1.665 = indi_v3_tb0.3) and its two
# survivors (results/v3_screen_yaw.md) vs pid_tuned, seeds 2-3, on step_yaw (speed 4) and motor_loss_0 (speed 1);
# v2 sim config. Hover effort over seeds 1-5 is in results/v3_hover_effort.md. Resumable. Ends with V3Y2_SCREEN_DONE.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project
D=$P/results/v3_screen_yaw2/runs
declare -A SPEED=([motor_loss_0]=1 [step_yaw]=4)
V2=(--sim v2 --imu-rate 1000 --erpm-drop 0.01 --vib-acc 1.0 --vib-gyr 0.05)
CONFIGS=(pid_tuned k2.733_c1.665 k2.733_c3.0 k4.0_c3.0)
pfile() { [ $1 = pid_tuned ] && echo $P/results/s2_tuning/pid/r1f/c05/params || echo $P/bench/params/indi_v3y_$1.params; }
run() {  # entry controller seed
	local out=$D/$1/$2/seed$3
	[ -f $out/metrics.json ] && return
	mkdir -p $out
	indi_project/docker/run.sh -n v3y2-$1-$2-$3 -t 900 -N python3 indi_project/bench/run_scenario.py --scenario $1 \
		--controller $2 --seed $3 --speed ${SPEED[$1]} --out $out "${V2[@]}" --params $(pfile $2) > $out/runner.log 2>&1
	python3 indi_project/bench/metrics.py $out/flight.ulg > $out/metrics.log 2>&1
	echo "[v3y2] $(date +%T) done $1 $2 seed$3"
}
for e in step_yaw motor_loss_0; do
	for s in 2 3; do for c in "${CONFIGS[@]}"; do run $e $c $s & done; done
	wait
done
echo V3Y2_SCREEN_DONE
