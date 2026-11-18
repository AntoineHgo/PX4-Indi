#!/bin/bash
# one draw per container; --n 20 keeps the draw identical to the dry-run scan (campaign(seed,n) depends on n).
# g3_run.py has no stop index, so g3_one.py (scratch wrapper, not part of the runner) restricts campaign() to one index.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
R=indi_flight/results/g3_pretest_s112
BP=indi_flight/bench/params/quad5in_indi_g1.params
for spec in "1 3 seed1" "3 18 seed3" "2 18 seed2"; do
  set -- $spec
  indi_project/docker/run.sh -n g3pre_$3 -t 1500 -- python3 $R/g3_one.py --seed $1 --n 20 --start $2 --base-params $BP --out-root $R/$3 --timeout-s 1200
  echo "$3 docker_rc=$?"
done
