#!/bin/bash
# G3 pre-test re-fly S197 (Q24 B, GNSS mismatch +-50 ms): same command as freeze10_s193/g3_pretest/fly_all.sh, seed 173, n 300.
# Only draws whose plant changed are flown (mismatched draws). Usage: bash fly_all.sh IDX [IDX...]; runs with g3_done.json are skipped.
# Scoring is a separate step (score_all.sh).
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi || exit 1
R=indi_flight/results/g3_pretest_q24_s197
for i in "$@"; do
  d=$(printf '%s/run_%03d' $R $i)
  [ -f "$d/g3_done.json" ] && continue
  timeout 1700 indi_project/docker/run.sh -n g3p197_$i -t 1500 -- python3 indi_flight/bench/g3_run.py --seed 173 --n 300 \
    --start $i --stop $i --base-params indi_flight/results/g5_freeze_s157/params.params \
    --out-root $R --timeout-s 1200 > $R/stream_$i.txt 2>&1
  echo "$(date +%H:%M:%S) idx=$i rc=$?" >> $R/progress.txt
done
echo "$(date +%H:%M:%S) BATCH_END $*" >> $R/progress.txt
