#!/bin/bash
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi || exit 1
R=indi_flight/results/freeze10_cand_s191/g3_matched
timeout 1000 bash indi_flight/bench/g3_score_docker.sh $R > $R/SCORE_KEY1.txt 2>&1
for r in $R/run_*; do
  [ -f $r/g3_checks.json ] && python3 -c "
import json,sys; j=json.load(open('$r/g3_checks.json')); print('KEY1', '$(basename $r)', 'pass' if j.get('pass') else 'FAIL')" >> $R/SCORE_KEY1.txt
done
mkdir -p $R/key2
: > $R/SCORE_KEY2.txt
grep -E '^run_[0-9]+ --t0' $R/SCORE_KEY1.txt | while read -r run args; do
  timeout 600 indi_project/docker/run.sh -n f10b_k2 -t 500 -- python3 indi_flight/bench/g3_checks_key2.py $R/$run $args --out $R/key2 >> $R/SCORE_KEY2.txt 2>&1
done
echo "SCORING_DONE $(date +%H:%M:%S)" >> $R/progress.txt
