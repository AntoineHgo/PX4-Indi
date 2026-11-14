#!/usr/bin/env bash
# v3 yaw stage-1 screening (session 46, O-12, D-v3-tb): MC_INDI_K_Y {2.733, 4.0, 5.5} x MC_INDI_YAW_CUT {1.665, 3.0}
# on indi_v3_tb0.3 (Tb 0.3, outer gains = tuned PID's), vs pid_tuned, seed 1, on step_yaw (speed 4), motor_loss_0
# and hover (speed 1, effort check); v2 sim config. Resumable. Ends with V3Y_SCREEN_DONE.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project
D=$P/results/v3_screen_yaw/runs
declare -A SPEED=([motor_loss_0]=1 [step_yaw]=4 [hover]=1)
V2=(--sim v2 --imu-rate 1000 --erpm-drop 0.01 --vib-acc 1.0 --vib-gyr 0.05)
CONFIGS=(pid_tuned)
for ky in 2.733 4.0 5.5; do for yc in 1.665 3.0; do CONFIGS+=(k${ky}_c${yc}); done; done
pfile() { [ $1 = pid_tuned ] && echo $P/results/s2_tuning/pid/r1f/c05/params || echo $P/bench/params/indi_v3y_$1.params; }
run() {  # entry controller seed
	local out=$D/$1/$2/seed$3
	[ -f $out/metrics.json ] && return
	mkdir -p $out
	indi_project/docker/run.sh -n v3y-$1-$2-$3 -t 900 -N python3 indi_project/bench/run_scenario.py --scenario $1 \
		--controller $2 --seed $3 --speed ${SPEED[$1]} --out $out "${V2[@]}" --params $(pfile $2) > $out/runner.log 2>&1
	python3 indi_project/bench/metrics.py $out/flight.ulg > $out/metrics.log 2>&1
	echo "[v3y] $(date +%T) done $1 $2 seed$3"
}
for e in step_yaw motor_loss_0 hover; do
	for c in "${CONFIGS[@]}"; do run $e $c 1 & done
	wait
done
echo V3Y_SCREEN_DONE
