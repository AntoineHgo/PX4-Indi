#!/usr/bin/env bash
# T145: re-fly G2-STEP 400 Hz (batch A) and 800 Hz step_roll (batch B) with a firmware built from HEAD.
# Build step gates the flights (same pattern as results/g2_step_s64/fly.sh). Run from the repo root.
G=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/g2_clean_s68
P400=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/g2_step_s64_400/indi.params
P800=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/g2_step_s64/indi.params
fly_one() { # $1=label $2=rate_hz $3=params $4=scenario $5=seed $6=dir (flight out is $6/$4_indi)
  mkdir -p $6
  indi_project/docker/run.sh -n s68_$1 -t 900 -- python3 indi_flight/bench/run_scenario.py --scenario $4 \
    --controller indi --model quad5in --sim v2 --rate-hz $2 --seed $5 --speed 4 \
    --params $3 --out $6/$4_indi > $6/$4_indi.stdout 2>&1; echo "$1 rc=$?" >> $G/done.txt; }
mkdir -p $G/b800
git rev-parse HEAD > $G/head.txt; git status --short -uno >> $G/head.txt
indi_project/docker/run.sh -n s68_build -t 2400 -- make px4_sitl_default > $G/build.log 2>&1; echo "build rc=$?" >> $G/done.txt
grep -q "build rc=0" $G/done.txt || { echo "BUILD FAILED" >> $G/done.txt; echo ALLDONE >> $G/done.txt; exit 1; }
for seed in 1 2 3; do
  ( for s in step_roll step_pitch step_yaw; do fly_one A_s${seed}_$s 400 $P400 $s $seed $G/steps_seed$seed; done ) &
done
wait
for k in 1 2 3 4 5; do fly_one B_r$k 800 $P800 step_roll 1 $G/b800/r$k & done
wait
echo ALLDONE >> $G/done.txt
