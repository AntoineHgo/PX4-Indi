#!/bin/bash
# G3 pre-test S173: first 20 draws (idx 0-19) of the G3 campaign, master seed 173, n=300, freeze params
# (results/g5_freeze_s157/params.params), firmware aa4fd2654a (D-JFF-OFFB). Serial, one container per run.
# Usage (repo root): bash indi_flight/results/g3_pretest_s173/fly.sh [first] [last]; done runs are skipped.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
R=indi_flight/results/g3_pretest_s173
A=${1:-0}; B=${2:-19}
for i in $(seq $A $B); do
  d=$(printf '%s/run_%03d' $R $i)
  [ -f "$d/flight.ulg" ] && continue
  indi_project/docker/run.sh -n g3p173_$i -t 1500 -- python3 indi_flight/bench/g3_run.py --seed 173 --n 300 \
    --start $i --stop $i --base-params indi_flight/results/g5_freeze_s157/params.params \
    --out-root indi_flight/results/g3_pretest_s173 --timeout-s 1200 > $R/stream_$i.txt 2>&1
  echo "$(date +%H:%M:%S) idx=$i docker_rc=$?" >> $R/progress.txt
done
echo "$(date +%H:%M:%S) BATCH_END $A-$B" >> $R/progress.txt
touch $R/FLY_DONE
