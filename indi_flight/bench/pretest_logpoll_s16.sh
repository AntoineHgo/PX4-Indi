#!/bin/bash
# S16 logger-rate pre-test: step_roll 800 Hz, (speed 1, poll sensor_gyro) and (speed 4, poll actuator_motors).
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
R=indi_flight/results/pretest_simstep_s16
for spec in "1 sensor_gyro" "4 actuator_motors"; do
  set -- $spec
  d=$R/step_roll_sp$1_$2
  indi_project/docker/run.sh -n pre_s16_lp_$1 -t 400 -- python3 indi_flight/bench/run_scenario.py --scenario step_roll --controller pid_default --model quad5in --seed 1 --speed $1 --rate-hz 800 --log-poll $2 --out $d > $d.stdout.log 2>&1
  echo "step_roll speed=$1 poll=$2 docker_rc=$?" >> $R/status.txt
done
