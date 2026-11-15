#!/usr/bin/env bash
# Stage-8 smoke with SENS_GNSS0_DELAY 0 before freezing indi_pos_v3 (D-s8-gnss-delay): T1 hover seeds 1-2 (effort
# criterion), H1 traj_circle_fast seed 1, T5 seed 2; pid_tuned and indi_pos_v3 (jerk LPF build). Seen entries only.
# Ends S8M_DONE, resumable by re-running.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project
D=$P/results/s8m_smoke_gnss0
mkdir -p $D
V2=(--sim v2 --imu-rate 1000 --erpm-drop 0.01 --vib-acc 1.0 --vib-gyr 0.05 --gnss-delay 0)
PID=$P/results/s2_tuning/pid/r1f/c05/params
IPOS=$P/bench/params/indi_pos_v3.params
run() {  # entry controller params seed
	local out=$D/$1/$2/seed$4
	[ -f $out/metrics.json ] && return
	mkdir -p $out
	indi_project/docker/run.sh -n s8m-$1-$2-$4 -t 900 -N python3 indi_project/bench/run_scenario.py --scenario $1 \
		--controller $2 --seed $4 --speed 1 --out $out "${V2[@]}" --params $3 > $out/runner.log 2>&1
	python3 indi_project/bench/metrics.py $out/flight.ulg > $out/metrics.log 2>&1
	echo "[s8m] $(date +%T) done $1 $2 seed$4"
}
run hover pid_tuned $PID 1 & run hover indi_pos_v3 $IPOS 1 & run hover pid_tuned $PID 2 & run hover indi_pos_v3 $IPOS 2 & wait
run traj_circle_fast pid_tuned $PID 1 & run traj_circle_fast indi_pos_v3 $IPOS 1 &
run traj_lemniscate pid_tuned $PID 2 & run traj_lemniscate indi_pos_v3 $IPOS 2 & wait
echo S8M_DONE
