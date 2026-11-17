#!/bin/bash
# S56: roll M3a at 400 Hz controller rate, defaults ACT_TC 0.05 lead 1, P8, AMP 0.001, seeds 1 and 2.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
D=indi_flight/results/stage3_s57_pre/roll_m3a_400
for s in 1 2; do n=roll400_s$s
indi_project/docker/run.sh -n s56r$n -t 900 "python3 indi_flight/bench/run_scenario.py --scenario hover_long --controller indi_m3a --seed $s --speed 4 --model quad5in --rate-hz 400 --params $D/roll400.params --out $D/$n" > $D/${n}_stdout.log 2>&1
indi_project/docker/run.sh -n s56rp$n -t 600 "bash -c 'python3 indi_flight/bench/check_rates.py $D/$n/flight.ulg > $D/${n}_rates.txt 2>&1; python3 indi_flight/bench/pretest_gate.py $D/$n/flight.ulg $D/${n}_gate.md > $D/${n}_gate_stdout.txt 2>&1; python3 indi_flight/bench/m3a_csv.py $D/$n/flight.ulg 0 $D/$n.csv; python3 indi_flight/bench/m3a_margins_pretest.py $D/$n.csv 1 60 10 400 > $D/${n}_margins.txt 2>&1'" > $D/${n}_post.log 2>&1
done
echo ALLDONE > $D/done.txt
