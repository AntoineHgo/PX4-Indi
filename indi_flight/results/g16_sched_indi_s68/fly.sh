#!/usr/bin/env bash
# T147: same-seed INDI step_roll repeats WITH the G1.6 determinism flags (--sched --sched-anchor, as in
# bench/g16_sched_set.sh: arm, offboard and setpoints played by PX4 in sim time). No --paused-start (not used
# by the G1.6 set). Logging at the runner default (--log-from-start). Firmware: build/px4_sitl_default, not rebuilt.
# Usage: bash fly.sh pre   (r400_1 alone, pre-test)
#        bash fly.sh rest  (r400_2..5 and r800_1..5, at most 5 in parallel; writes ALLDONE at the end)
G=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/g16_sched_indi_s68
P400=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/g2_step_s64_400/indi.params
P800=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/g2_step_s64/indi.params
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi || exit 1
mkdir -p $G

fly_one() { # $1=label $2=rate_hz $3=params (flight out is $G/$1/step_roll_indi)
  local d=$G/$1
  mkdir -p $d
  indi_project/docker/run.sh -n s68s_$1 -t 900 -- python3 indi_flight/bench/run_scenario.py --scenario step_roll \
    --controller indi --model quad5in --sim v2 --rate-hz $2 --seed 1 --speed 4 --sched --sched-anchor \
    --params $3 --out $d/step_roll_indi > $d/step_roll_indi.stdout 2>&1
  echo "$1 rc=$?" >> $G/done.txt
}

case "$1" in
  pre)
    git rev-parse HEAD > $G/head.txt; git status --short -uno >> $G/head.txt
    fly_one r400_1 400 $P400
    ;;
  rest)
    flights="r400_2:400:$P400 r400_3:400:$P400 r400_4:400:$P400 r400_5:400:$P400 r800_1:800:$P800 r800_2:800:$P800 r800_3:800:$P800 r800_4:800:$P800 r800_5:800:$P800"
    for f in $flights; do
      IFS=: read -r label rate params <<< "$f"
      while [ "$(jobs -rp | wc -l)" -ge 5 ]; do sleep 5; done
      fly_one $label $rate $params &
    done
    wait
    echo ALLDONE >> $G/done.txt
    ;;
  *) echo "usage: fly.sh pre|rest" >&2; exit 2 ;;
esac
