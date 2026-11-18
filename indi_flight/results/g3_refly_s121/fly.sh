#!/bin/bash
# S121 INDI re-fly of T118 idx 0/21/49 (runner now sets MC_RATE_CTL_TYPE 1). Master seed 117, campaign n=60.
# Usage: fly.sh <parallel streams> <index>...   One container per run; progress in progress.txt.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
R=indi_flight/results/g3_refly_s121
BP=indi_flight/bench/params/quad5in_indi_g1.params
P=$1; shift
one() {
  i=$1
  indi_project/docker/run.sh -n g3r121_$i -t 1500 -- python3 indi_flight/bench/g3_run.py --seed 117 --n 60 \
    --start $i --stop $i --base-params indi_flight/bench/params/quad5in_indi_g1.params \
    --out-root indi_flight/results/g3_refly_s121 --timeout-s 1200 > $R/stream_$i.txt 2>&1
  echo "$(date +%H:%M:%S) idx=$i docker_rc=$?" >> $R/progress.txt
}
export -f one; export R
printf '%s\n' "$@" | xargs -P "$P" -I{} bash -c 'one {}'
echo "$(date +%H:%M:%S) BATCH_END $*" >> $R/progress.txt
