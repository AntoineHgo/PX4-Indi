#!/usr/bin/env bash
# usage: fly.sh <indi|pid> <seed>   (G5.10 SAT part, freeze-9 config, nominal plant)
cd "$(dirname "$0")/../../.." || exit 1
R=indi_flight/results/g510_setup_s184; P=indi_flight/results/g5_freeze_s157/params.params
c=$1; s=$2; o=$R/${c}_satF_s$s
X=; [ $c = indi ] && X="--params $P"
timeout 1000 indi_project/docker/run.sh -n s184f${c}_s$s -t 900 -- python3 indi_flight/bench/run_scenario.py --controller $c $X \
  --model quad5in --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0 \
  --seed $s --scenario sat_sustained --out $o > $o.stdout.log 2>&1
python3 indi_flight/bench/g510_score_motors.py $o > $o.score.txt 2>&1; cat $o.score.txt
