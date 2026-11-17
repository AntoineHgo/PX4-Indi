#!/usr/bin/env bash
# T149 (a30_v1v2_s68): does the --sim v2 model break same-seed determinism?
# Scenario step_roll, speed 4, controller pid_default, model quad5in, seed 1, --sched --sched-anchor
# (command line of bench/g16_sched_set.sh, line 11). Wall timeout 600 s, container s68v_<label>, 5 in parallel.
# G-v1: exactly the G1.6 command (sim v1 default).
# G-v2: same plus --sim v2.
# Usage: bash fly.sh pre   (r1 of each group)
#        bash fly.sh rest  (r2..r5 of each group, at most 5 in parallel; writes ALLDONE at the end)
R=/home/ahugo/Documents/Drotek/Codes/PX4-Indi
G=$R/indi_flight/results/a30_v1v2_s68
cd $R || exit 1
mkdir -p $G

fly_one() { # $1 = label: v1_rK (G-v1) or v2_rK (G-v2)
  local label=$1 grp run simarg=""
  case $label in
    v1_*) grp=G-v1 ;;
    v2_*) grp=G-v2; simarg="--sim v2" ;;
  esac
  run=r${label#*_r}
  local d=$G/$grp/$run
  mkdir -p $d
  indi_project/docker/run.sh -n s68v_$label -t 600 -- python3 indi_flight/bench/run_scenario.py --scenario step_roll --controller pid_default --model quad5in --seed 1 --speed 4 --sched --sched-anchor $simarg --out indi_flight/results/a30_v1v2_s68/$grp/$run > $d/stdout.log 2>&1
  echo "$label rc=$?" >> $G/done.txt
}

case "$1" in
  pre)
    fly_one v1_r1 & fly_one v2_r1 &
    wait
    ;;
  rest)
    for l in v1_r2 v1_r3 v1_r4 v1_r5 v2_r2 v2_r3 v2_r4 v2_r5; do
      while [ "$(jobs -rp | wc -l)" -ge 5 ]; do sleep 5; done
      fly_one $l &
    done
    wait
    echo ALLDONE >> $G/done.txt
    ;;
esac
