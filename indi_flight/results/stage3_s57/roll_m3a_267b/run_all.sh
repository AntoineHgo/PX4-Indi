#!/bin/bash
# S57: roll M3a at 800/3 Hz, re-fly of the S56 set with MC_INDI_INJ_TP 7.5 (whole samples), seeds 1 and 2 in parallel.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
D=indi_flight/results/stage3_s57/roll_m3a_267b
one() { s=$1; n=roll267b_s$s
indi_project/docker/run.sh -n s57r$n -t 900 "python3 indi_flight/bench/run_scenario.py --scenario hover_long --controller indi_m3a --seed $s --speed 4 --model quad5in --rate-hz 267 --params $D/roll267b.params --out $D/$n" > $D/${n}_stdout.log 2>&1
indi_project/docker/run.sh -n s57rp$n -t 600 "bash -c 'python3 indi_flight/bench/check_rates.py $D/$n > $D/${n}_rates.txt 2>&1; python3 indi_flight/bench/pretest_gate.py $D/$n/flight.ulg $D/${n}_gate_preinj.md --delay 4 --length 15 > $D/${n}_gate_stdout.txt 2>&1; python3 indi_flight/bench/m3a_csv.py $D/$n/flight.ulg 0 $D/$n.csv; python3 indi_flight/bench/m3a_margins_pretest.py $D/$n.csv 1 60 7.5 266.6667 > $D/${n}_margins.txt 2>&1'" > $D/${n}_post.log 2>&1
}
one 1 & sleep 20; one 2 & wait
echo ALLDONE > $D/done.txt
