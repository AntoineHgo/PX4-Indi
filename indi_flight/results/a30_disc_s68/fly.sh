#!/usr/bin/env bash
# T148 (S68 discriminator): same-seed step_roll flights at 400 Hz, seed 1, speed 4, quad5in, --sched --sched-anchor.
# G-pid:  --controller pid --sim v2, params results/stage3_s61/pid.params (most recent quad5in PID step params; those flights were 800 Hz)
# G-true: --controller indi --sim v2true (exact rotor speed in esc_rpm), params results/g2_step_s64_400/indi.params
# G-lost: --controller indi --sim v2, params results/a30_disc_s68/indi_lost.params (g2 params + SIM_GZ_ERPM_LOSS 15)
# Usage: bash fly.sh pre   (one flight per group, pre-test)
#        bash fly.sh rest  (4 more per group, at most 5 in parallel; writes ALLDONE at the end)
R=/home/ahugo/Documents/Drotek/Codes/PX4-Indi
G=$R/indi_flight/results/a30_disc_s68
PID_P=$R/indi_flight/results/stage3_s61/pid.params
TRUE_P=$R/indi_flight/results/g2_step_s64_400/indi.params
LOST_P=$G/indi_lost.params
cd $R || exit 1
mkdir -p $G

fly_one() { # $1=label (pid_N | true_N | lost_N); flight out is $G/$1/step_roll_<controller>
  local label=$1 ctrl sim params d
  case $label in
    pid_*)  ctrl=pid;  sim=v2;     params=$PID_P ;;
    true_*) ctrl=indi; sim=v2true; params=$TRUE_P ;;
    lost_*) ctrl=indi; sim=v2;     params=$LOST_P ;;
  esac
  d=$G/$label
  mkdir -p $d
  indi_project/docker/run.sh -n s68d_$label -t 900 -- python3 indi_flight/bench/run_scenario.py --scenario step_roll \
    --controller $ctrl --model quad5in --sim $sim --rate-hz 400 --seed 1 --speed 4 --sched --sched-anchor \
    --params $params --out $d/step_roll_$ctrl > $d/step_roll_$ctrl.stdout 2>&1
  echo "$label rc=$?" >> $G/done.txt
}

case "$1" in
  pre)
    git rev-parse HEAD > $G/head.txt; git status --short -uno >> $G/head.txt
    fly_one pid_1 & fly_one true_1 & fly_one lost_1 &
    wait
    ;;
  rest)
    for l in pid_2 pid_3 pid_4 pid_5 true_2 true_3 true_4 true_5 lost_2 lost_3 lost_4 lost_5; do
      while [ "$(jobs -rp | wc -l)" -ge 5 ]; do sleep 5; done
      fly_one $l &
    done
    wait
    echo ALLDONE >> $G/done.txt
    ;;
  *) echo "usage: fly.sh pre|rest" >&2; exit 2 ;;
esac
