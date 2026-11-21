#!/bin/bash
# G3 pre-test re-fly S190 on the Q22 box: same command as S173 (g3_pretest_s173/fly.sh), master seed 173, n 300, idx 0-19,
# but g3_sample.py now implements the Q22 box (e x[0.8,1.2], tau_up/down x[0.5,3]); run 17 old (e 1.52) is replaced by the new draw 17.
# Freeze params results/g5_freeze_s157/params.params (has MC_INDI_POS_EN 1). Serial, one container per run (px4-indi-g3p190_<i>).
# Usage (any cwd): bash indi_flight/results/g3_pretest_s190/fly_all.sh [first] [last]; runs with g3_done.json are skipped (resume).
# After the last run both scorers run (key 1 g3_checks.py, key 2 g3_checks_key2.py) unless SKIP_SCORE=1.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi || exit 1
R=indi_flight/results/g3_pretest_s190
A=${1:-0}; B=${2:-19}
for i in $(seq $A $B); do
  d=$(printf '%s/run_%03d' $R $i)
  [ -f "$d/g3_done.json" ] && continue
  docker ps -q --filter "name=px4-indi-g3p190_" | xargs -r docker stop >/dev/null 2>&1
  timeout 1700 indi_project/docker/run.sh -n g3p190_$i -t 1500 -- python3 indi_flight/bench/g3_run.py --seed 173 --n 300 \
    --start $i --stop $i --base-params indi_flight/results/g5_freeze_s157/params.params \
    --out-root $R --timeout-s 1200 > $R/stream_$i.txt 2>&1
  echo "$(date +%H:%M:%S) idx=$i rc=$?" >> $R/progress.txt
done
echo "$(date +%H:%M:%S) BATCH_END $A-$B" >> $R/progress.txt
touch $R/FLY_DONE
[ "${SKIP_SCORE:-0}" = 1 ] && exit 0
# Key 1: g3_score.sh (window/mode/wind/sag args derived per run) inside the sim image (scipy); stdout = "run args" lines.
timeout 1000 bash indi_flight/bench/g3_score_docker.sh $R > $R/SCORE_KEY1.txt 2>&1
for r in $R/run_*; do
  [ -f $r/g3_checks.json ] && python3 -c "
import json,sys; j=json.load(open('$r/g3_checks.json')); print('KEY1', '$(basename $r)', 'pass' if j.get('pass') else 'FAIL')" >> $R/SCORE_KEY1.txt
done
# Key 2: same per-run args (from the key-1 lines), outputs in $R/key2/<run>.json
mkdir -p $R/key2
: > $R/SCORE_KEY2.txt
grep -E '^run_[0-9]+ --t0' $R/SCORE_KEY1.txt | while read -r run args; do
  # shellcheck disable=SC2086
  timeout 600 indi_project/docker/run.sh -n g3p190_k2 -t 500 -- python3 indi_flight/bench/g3_checks_key2.py $R/$run $args --out $R/key2 >> $R/SCORE_KEY2.txt 2>&1
done
echo "SCORING_DONE $(date +%H:%M:%S)" >> $R/progress.txt
