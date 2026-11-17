#!/usr/bin/env bash
# T151 (a32_load_s69): is the A-32 same-seed spread caused by host load (parallel runs), not by a code change?
# Exact G1.6 command (bench/g16_sched_set.sh line 11, step_roll, speed 4, sim v1, pid_default, seed 1, --sched --sched-anchor).
# G-seq: 5 runs strictly sequential (as S32). G-par: 5 runs started together (as T149 'rest').
# Usage: bash fly.sh   (seq first, then par; writes ALLDONE)
R=/home/ahugo/Documents/Drotek/Codes/PX4-Indi
G=$R/indi_flight/results/a32_load_s69
cd $R || exit 1
docker ps -q --filter name=s69l_ | xargs -r docker stop >/dev/null
fly_one() { # $1 group, $2 run
  local d=indi_flight/results/a32_load_s69/$1/$2; mkdir -p $R/$d; local t0=$(date +%s)
  indi_project/docker/run.sh -n s69l_$1_$2 -t 600 -- python3 indi_flight/bench/run_scenario.py --scenario step_roll --controller pid_default --model quad5in --seed 1 --speed 4 --sched --sched-anchor --out $d >$R/$d/stdout.txt 2>&1
  echo "$1 $2 rc=$? wall=$(( $(date +%s) - t0 ))s" >> $G/done.txt
}
for r in r1 r2 r3 r4 r5; do fly_one G-seq $r; done
for r in r1 r2 r3 r4 r5; do fly_one G-par $r & done; wait
echo ALLDONE >> $G/done.txt
