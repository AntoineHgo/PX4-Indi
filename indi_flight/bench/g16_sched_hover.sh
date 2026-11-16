#!/bin/bash
# G1.6(a) pre-check with the sim-time player: 5 identical-seed hovers at speed 4, then the second-key instants.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
R=indi_flight/results/g16_sched_s24
mkdir -p $R
for r in r1 r2 r3 r4 r5; do
  indi_project/docker/run.sh -n g16sched_$r -t 300 -- python3 indi_flight/bench/run_scenario.py --scenario hover --controller pid_default --model quad5in --seed 1 --speed 4 --sched --out $R/hover_$r > $R/hover_${r}_stdout.log 2>&1
  echo "$r docker_rc=$?" >> $R/status.txt
  indi_project/docker/run.sh -n g16sk_$r -t 300 -- python3 indi_flight/bench/second_key_player.py $R/hover_$r/flight.ulg $R/hover_$r/instants.json >> $R/status.txt 2>&1
done
echo DONE >> $R/status.txt
