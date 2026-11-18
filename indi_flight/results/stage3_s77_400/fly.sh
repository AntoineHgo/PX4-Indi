#!/usr/bin/env bash
# S77 A-34 closing: 400 Hz rate-loop margins, S57 file tb 0 and tb 1.0, sequential (D-RATE-BLD precondition 1 at 400 Hz).
# Build gates the flights. Run from the repo root: bash indi_flight/results/stage3_s77_400/fly.sh
G=indi_flight/results/stage3_s77_400
git rev-parse HEAD > $G/head.txt; git status --short -uno >> $G/head.txt
indi_project/docker/run.sh -n s77q_build -t 2400 -- make px4_sitl_default > $G/build.log 2>&1; echo "build rc=$?" >> $G/done.txt
grep -q "build rc=0" $G/done.txt || { echo "BUILD FAILED" >> $G/done.txt; echo ALLDONE >> $G/done.txt; exit 1; }
fly_one() { # $1 = tb
  n=$1
  indi_project/docker/run.sh -n s77q_$n -t 900 -- python3 indi_flight/bench/run_scenario.py --scenario hover_long \
    --controller indi --model quad5in --sim v2 --rate-hz 400 --seed 1 --speed 4 \
    --params $G/$n.params --out $G/$n > $G/${n}_stdout.log 2>&1; echo "$n fly rc=$?" >> $G/done.txt
  indi_project/docker/run.sh -n s77qp$n -t 600 -- bash -c "python3 indi_flight/bench/pretest_gate.py $G/$n/flight.ulg $G/${n}_gate.md > $G/${n}_gate_stdout.txt 2>&1; python3 indi_flight/bench/m3a_csv.py $G/$n/flight.ulg 0 $G/$n.csv && python3 indi_flight/bench/m3a_margins_pretest.py $G/$n.csv 1 60 10 400 > $G/${n}_margins.txt 2>&1" > $G/${n}_post.log 2>&1
  echo "$n post rc=$?" >> $G/done.txt; }
for n in tb0 bld1.0; do fly_one $n; done
wait
echo ALLDONE >> $G/done.txt
