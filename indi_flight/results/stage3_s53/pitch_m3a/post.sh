#!/bin/bash
# usage: post.sh name amp  (run in container, repo root). S53 copy of S52 post.sh + pre-injection gate window.
D=indi_flight/results/stage3_s53/pitch_m3a; n=$1; a=$2
python3 indi_flight/results/stage2_s40/pretest_inj/checks.py $D/$n $a 20 3 > $D/${n}_checks.txt 2>&1; echo "checks rc $?"
python3 indi_flight/bench/pretest_gate.py $D/$n/flight.ulg $D/${n}_gate_preinj.md --delay 4 --length 15 > $D/${n}_gate_stdout.txt 2>&1; echo "gate rc $?"
python3 indi_flight/bench/m3a_csv.py $D/$n/flight.ulg 1 $D/$n.csv
python3 indi_flight/bench/m3a_margins_pretest.py $D/$n.csv > $D/${n}_margins.txt 2>&1; echo "margins rc $?"
