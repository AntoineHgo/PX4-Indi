#!/usr/bin/env bash
# S92 attitude-break 267 Hz reported cell (D-RATE267, mission 250 Hz) (roll), RAMP 0.06, same pipeline as batch.sh. Run from repo root.
D=indi_flight/results/stage5_s91_attbreak
for C in "1 267"; do
  set -- $C; N=ax$1_r$2_s1_a0.06
  $D/fly.sh $1 $2 1 0.06
  indi_project/docker/run.sh -n s92m$N -t 240 -- python3 indi_flight/bench/ratesp_csv.py $D/$N/flight.ulg $(($1-1)) \
    $D/${N}_att.csv --Tp 10 --fmin 0.2 --fmax 20 --margins > $D/${N}_margins.json 2> $D/${N}_margins.err
done
echo BATCH DONE
