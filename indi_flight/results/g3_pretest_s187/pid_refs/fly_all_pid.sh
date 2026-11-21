#!/bin/bash
# G3 pre-test PID reference flights (S188), same draws (seed 173, n 300) as the failing INDI runs of g3_pretest_s187, stock PID rate loop.
# Serial, one container per run (g3pid188_<i>), priority order. Runs with g3_done.json are skipped (resume).
# Usage (any cwd): bash indi_flight/results/g3_pretest_s187/pid_refs/fly_all_pid.sh   (SKIP_SCORE=1 skips scoring)
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi || exit 1
R=indi_flight/results/g3_pretest_s187/pid_refs
RUNS="10 16 0 5 17 2 3 8 9 13"
for i in $RUNS; do
  d=$(printf '%s/run_%03d' $R $i)
  [ -f "$d/g3_done.json" ] && continue
  if [ -d "$d" ]; then mv "$d" "$d.incomplete_$(date +%H%M%S)"; fi  # unfinished earlier attempt: keep, refly
  docker ps -q --filter "name=g3pid188_" | xargs -r docker stop >/dev/null 2>&1
  timeout 1700 python3 $R/fly_pid_run.py $i > $R/stream_$i.txt 2>&1
  echo "$(date +%H:%M:%S) idx=$i rc=$?" >> $R/progress.txt
done
echo "$(date +%H:%M:%S) BATCH_END" >> $R/progress.txt
[ "${SKIP_SCORE:-0}" = 1 ] && exit 0
# note: g3_score.sh globs run_*, so move *.incomplete_* dirs away before scoring
mkdir -p $R/_incomplete; mv $R/run_*.incomplete_* $R/_incomplete/ 2>/dev/null
timeout 1000 bash indi_flight/bench/g3_score_docker.sh $R > $R/SCORE_PID_KEY1.txt 2>&1
for r in $R/run_[0-9][0-9][0-9]; do
  [ -f $r/g3_checks.json ] && python3 -c "
import json; j=json.load(open('$r/g3_checks.json')); print('KEY1', '$(basename $r)', 'pass' if j.get('pass') else 'FAIL')" >> $R/SCORE_PID_KEY1.txt
done
mkdir -p $R/key2
: > $R/SCORE_PID_KEY2.txt
grep -E '^run_[0-9]+ --t0' $R/SCORE_PID_KEY1.txt | while read -r run args; do
  # shellcheck disable=SC2086
  timeout 600 indi_project/docker/run.sh -n g3pid188_k2 -t 500 -- python3 indi_flight/bench/g3_checks_key2.py $R/$run $args --out $R/key2 >> $R/SCORE_PID_KEY2.txt 2>&1
done
echo "SCORING_DONE $(date +%H:%M:%S)" >> $R/progress.txt
touch $R/DONE
