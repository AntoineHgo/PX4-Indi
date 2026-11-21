#!/bin/bash
# fix probe S190: same command as fly_all.sh (freeze params), HEAD 2d92dbcf59 build. Usage: fly.sh idx...
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi || exit 1
R=indi_flight/results/g3_pretest_s187/fix_s190
for i in "$@"; do
  docker ps -q --filter "name=px4-indi-g3f190_" | xargs -r docker stop >/dev/null 2>&1
  timeout 1700 indi_project/docker/run.sh -n g3f190_$i -t 1500 -- python3 indi_flight/bench/g3_run.py --seed 173 --n 300 \
    --start $i --stop $i --base-params indi_flight/results/g5_freeze_s157/params.params \
    --out-root $R --timeout-s 1200 > $R/stream_$i.txt 2>&1
  echo "$(date +%H:%M:%S) idx=$i rc=$?" >> $R/progress.txt
done
echo DONE >> $R/progress.txt
