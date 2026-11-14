#!/usr/bin/env bash
# First run-time check of D-omega2 wiring (build/px4_sitl_omega2, CA_R_W_MAX 1000): frozen v1 INDI params + v2_fac,
# v2 sim (eRPM model, 1000 Hz IMU, vibration, 1 % eRPM drops). One hover (speed 1) and one step_roll (speed 4), seed 1.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
D=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project/results/s2_omega2_check
B=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/build/px4_sitl_omega2
run() {  # scenario speed
	mkdir -p $D/$1$SFX
	indi_project/docker/run.sh -n om2-$1 -t 600 -N -e PX4_INDI_BUILD=$B python3 indi_project/bench/run_scenario.py \
		--scenario $1 --controller indi_omega2 --seed 1 --speed $2 --out $D/$1$SFX --sim v2 --imu-rate 1000 \
		--erpm-drop 0.01 --vib-acc 1.0 --vib-gyr 0.05 --params $D/indi_omega2.params > $D/$1$SFX/runner.log 2>&1
	python3 indi_project/bench/metrics.py $D/$1$SFX/flight.ulg >> $D/$1$SFX/runner.log 2>&1
}
# SFX=_log: re-fly after the logger commit (actuator_torque_measured logged)
run hover 1 & run step_roll 4 & wait
echo OMEGA2_CHECK_DONE
