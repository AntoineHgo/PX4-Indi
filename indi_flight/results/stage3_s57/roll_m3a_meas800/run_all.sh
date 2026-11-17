#!/bin/bash
# S57: roll M3a 800 Hz on the measured-rotor path (sim v2, CA_R_W_MAX 2700), defaults ACT_TC 0.05 lead 1, seeds 1-2.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
D=indi_flight/results/stage3_s57/roll_m3a_meas800
one() { s=$1; n=meas800_s$s
indi_project/docker/run.sh -n s57m$n -t 900 "python3 indi_flight/bench/run_scenario.py --scenario hover_long --controller indi_m3a --seed $s --speed 4 --model quad5in --rate-hz 800 --sim v2 --params $D/meas800.params --out $D/$n" > $D/${n}_stdout.log 2>&1
indi_project/docker/run.sh -n s57mp$n -t 600 "bash -c 'python3 indi_flight/bench/check_rates.py $D/$n > $D/${n}_rates.txt 2>&1; python3 indi_flight/bench/pretest_gate.py $D/$n/flight.ulg $D/${n}_gate_preinj.md --delay 4 --length 15 > $D/${n}_gate_stdout.txt 2>&1; python3 indi_flight/bench/m3a_csv.py $D/$n/flight.ulg 0 $D/$n.csv; python3 indi_flight/bench/m3a_margins_pretest.py $D/$n.csv 1 60 10 800 > $D/${n}_margins.txt 2>&1'" > $D/${n}_post.log 2>&1
}
one 1 & sleep 20; one 2 & wait
echo ALLDONE > $D/done.txt
