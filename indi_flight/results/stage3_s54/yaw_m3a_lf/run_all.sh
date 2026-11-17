#!/bin/bash
# S54 A-27: yaw M3a, bins 0.1-20 Hz, seed 1, binary built at 7522625b0f.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
D=indi_flight/results/stage3_s54/yaw_m3a_lf; n=yaw_s1
indi_project/docker/run.sh -n s54$n -t 900 "python3 indi_flight/bench/run_scenario.py --scenario hover_long --controller indi_m3a --seed 1 --speed 4 --model quad5in --params $D/yaw_lf.params --out $D/$n" > $D/${n}_stdout.log 2>&1
indi_project/docker/run.sh -n s54p$n -t 600 "bash -c 'python3 indi_flight/results/stage2_s40/pretest_inj/checks.py $D/$n 0.008 15 4 > $D/${n}_checks.txt 2>&1; python3 indi_flight/bench/pretest_gate.py $D/$n/flight.ulg $D/${n}_gate_preinj.md --delay 4 --length 10 > $D/${n}_gate_stdout.txt 2>&1; python3 indi_flight/bench/m3a_csv.py $D/$n/flight.ulg 2 $D/$n.csv; python3 indi_flight/bench/m3a_margins_pretest.py $D/$n.csv 0.1 20 10 > $D/${n}_margins.txt 2>&1'" > $D/${n}_post.log 2>&1
echo ALLDONE > $D/done.txt
