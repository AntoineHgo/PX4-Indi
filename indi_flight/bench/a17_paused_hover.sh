#!/bin/bash
# A-17 (s25): 5 identical-seed sched hovers with gz started paused and unpaused after PX4 start-up, then the
# Commander phase and second-key instants. Usage: a17_paused_hover.sh [runs...] (default r1 r2 r3 r4 r5)
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
R=indi_flight/results/a17_paused_s25
mkdir -p $R
RUNS=${@:-r1 r2 r3 r4 r5}
for r in $RUNS; do
  indi_project/docker/run.sh -n a17p_$r -t 300 -- python3 indi_flight/bench/run_scenario.py --scenario hover --controller pid_default --model quad5in --seed 1 --speed 4 --sched --paused-start --out $R/hover_$r > $R/hover_${r}_stdout.log 2>&1
  echo "$r docker_rc=$?" >> $R/status.txt
  indi_project/docker/run.sh -n a17pk_$r -t 300 -- python3 indi_flight/bench/second_key_player.py $R/hover_$r/flight.ulg $R/hover_$r/instants.json >> $R/status.txt 2>&1
  indi_project/docker/run.sh -n a17pp_$r -t 300 -- python3 indi_flight/bench/a17_commander_phase.py $R/hover_$r/flight.ulg $R/hover_$r/phase.json >> $R/status.txt 2>&1
done
echo DONE >> $R/status.txt
