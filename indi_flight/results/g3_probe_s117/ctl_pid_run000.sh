#!/bin/bash
# PID control flight on the run_000 draw (acro watchdog trip, S117)
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
indi_project/docker/run.sh -n g3p117_pid0 -t 1500 -- python3 indi_flight/bench/run_scenario.py --scenario stick_zsine_o6 --controller pid_default --model quad5in --sim v2 --rate-hz 800 --seed 1020732965 --sim-seed 736238613 --out indi_flight/results/g3_probe_s117/ctl_pid_run000 --params indi_flight/results/g3_probe_s117/run_000/g3_params.txt --stick-mode acro --model-variant tau=2.345751,tau_down=2.764887,mass=0.763862,ixx=0.853671,iyy=1.081126,izz=0.750016 --dly-act 5 --dly-imu 5 --vib-acc 1.314647 --vib-gyr 0.065732 --gps-dly 88 --gnss-delay 88 > indi_flight/results/g3_probe_s117/ctl_pid_run000.txt 2>&1
echo "pid0 rc=$?" >> indi_flight/results/g3_probe_s117/progress.txt
