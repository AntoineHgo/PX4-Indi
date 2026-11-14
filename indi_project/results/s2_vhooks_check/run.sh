#!/usr/bin/env bash
# Smoke check of the stage-2 held-out sim hooks (V3 eRPM latency, V4 timed eRPM loss, V6 thrust sag) before the
# v2 held-out set is frozen: PID defaults + v2_fac, build/px4_sitl_omega2, seed 1, speed 4. Harness check only.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
D=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project/results/s2_vhooks_check
B=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/build/px4_sitl_omega2
run() {  # scenario
	mkdir -p $D/$1
	indi_project/docker/run.sh -n vh-$1 -t 600 -N -e PX4_INDI_BUILD=$B python3 indi_project/bench/run_scenario.py \
		--scenario $1 --controller pid --seed 1 --speed 4 --out $D/$1 --sim v2 --imu-rate 1000 \
		--erpm-drop 0.01 --vib-acc 1.0 --vib-gyr 0.05 \
		--params indi_project/bench/params/v2_fac.params > $D/$1/runner.log 2>&1
	python3 indi_project/bench/metrics.py $D/$1/flight.ulg >> $D/$1/runner.log 2>&1
}
run v2_drop_att & run v2_sag_att & run v2_lat_att & wait
echo VHOOKS_DONE
