#!/usr/bin/env bash
# batch.sh NAME...: fly each variant in turn (one flight at a time), log verdicts to restore264/batch.log
W=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/g3_refly_actc_s212/restore264
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
for n in "$@"; do
  [ "$(docker ps -q | wc -l)" = 0 ] || { echo "stray container, stop" >>$W/batch.log; exit 1; }
  bash $W/scripts/fly.sh $n
  timeout 1300 $W/scripts/wait_result.sh $n >>$W/batch.log 2>&1
  echo "== $n" >>$W/batch.log; python3 $W/scripts/tilt.py $W/indi_$n/run_024/flight.ulg >>$W/batch.log 2>&1
done
echo BATCH_DONE >>$W/batch.log
