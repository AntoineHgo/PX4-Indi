#!/usr/bin/env bash
# Part B: G3 draws 02 and 05 re-flown with EKF GNSS delay = drawn latency (--override-gnss-matched), otherwise exactly g3_pretest_s190/fly_all.sh.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi || exit 1
R=indi_flight/results/freeze10_cand_s191/g3_matched; mkdir -p $R
for i in 2 5; do
  d=$(printf '%s/run_%03d' $R $i)
  [ -f "$d/g3_done.json" ] && continue
  timeout 1700 indi_project/docker/run.sh -n f10b_$i -t 1500 -- python3 indi_flight/bench/g3_run.py --seed 173 --n 300 \
    --start $i --stop $i --base-params indi_flight/results/g5_freeze_s157/params.params \
    --out-root $R --timeout-s 1200 --override-gnss-matched > $R/stream_$i.txt 2>&1
  echo "$(date +%H:%M:%S) idx=$i rc=$?" >> $R/progress.txt
done
touch $R/FLY_DONE
