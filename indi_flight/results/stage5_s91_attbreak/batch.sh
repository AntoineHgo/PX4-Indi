#!/usr/bin/env bash
# S91 attitude-break cells, serial, RAMP 0.06 (ax1 r400 = pre-test flight). Run from repo root.
D=indi_flight/results/stage5_s91_attbreak
for C in "2 400" "3 400" "1 800" "2 800" "3 800"; do
  set -- $C; N=ax$1_r$2_s1_a0.06
  $D/fly.sh $1 $2 1 0.06
  indi_project/docker/run.sh -n s91m$N -t 240 -- python3 indi_flight/bench/ratesp_csv.py $D/$N/flight.ulg $(($1-1)) \
    $D/${N}_att.csv --Tp 10 --fmin 0.2 --fmax 20 --margins > $D/${N}_margins.json 2> $D/${N}_margins.err
done
echo BATCH DONE
