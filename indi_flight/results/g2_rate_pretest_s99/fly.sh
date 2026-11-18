#!/usr/bin/env bash
# S99 G2 rate-loop margin pre-test: P1 pitch 800 Hz, P2 yaw 400 Hz. Recipe S57 (meas800, sim v2) with axis/rate changed only. Serial.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
G=indi_flight/results/g2_rate_pretest_s99
fly_one() { # $1 name, $2 csv axis, $3 rate-hz
  n=$1; ax=$2; hz=$3; D=$G/$n
  indi_project/docker/run.sh -n g2pt_$n -t 900 -- python3 indi_flight/bench/run_scenario.py --scenario hover_long --controller indi_m3a \
    --seed 1 --speed 4 --model quad5in --rate-hz $hz --sim v2 --params $G/${n/P/P}.params --out $D/s1 > $D/stdout.log 2>&1
  echo "$n fly rc=$?" >> $G/done.txt
  indi_project/docker/run.sh -n g2pp_$n -t 600 -- bash -c "python3 indi_flight/bench/check_rates.py $D/s1 > $D/rates.txt 2>&1; \
    python3 indi_flight/bench/pretest_gate.py $D/s1/flight.ulg $D/gate.md --delay 4 --length 15 > $D/gate_stdout.txt 2>&1; \
    python3 indi_flight/bench/m3a_csv.py $D/s1/flight.ulg $ax $D/s1.csv > $D/csv_stdout.txt 2>&1; \
    python3 indi_flight/bench/m3a_margins_pretest.py $D/s1.csv 1 60 10 $hz > $D/margins.txt 2>&1; \
    for a in 0 1 2; do python3 indi_flight/bench/m3a_csv.py $D/s1/flight.ulg \$a /tmp/x_\$a.csv >> $D/axis_check.txt 2>&1 || echo \"axis \$a: no injection\" >> $D/axis_check.txt; done" > $D/post.log 2>&1
  echo "$n post rc=$?" >> $G/done.txt
}
fly_one P1 1 800
fly_one P2 2 400
echo ALLDONE >> $G/done.txt
