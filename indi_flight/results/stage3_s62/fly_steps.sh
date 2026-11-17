#!/usr/bin/env bash
# S62: INDI attitude + torque steps after D-S3-ATT-STEP (da64bc26b3), seeds 1-3, same command as stage3_s61/fly_steps.sh.
# PID reference unchanged (stage3_s61, indi_vs_pid). Run from the repo root.
B=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/stage3_s62
indi_project/docker/run.sh -n s62build -t 2400 -- make px4_sitl_default > $B/build.log 2>&1; echo "build rc=$?" >> $B/done.txt
fly() { # scenario seed
  O=$B/steps_seed$2; mkdir -p $O
  indi_project/docker/run.sh -n s62_$1_$2 -t 900 -- python3 indi_flight/bench/run_scenario.py --scenario $1 \
    --controller indi --model quad5in --sim v2 --rate-hz 800 --seed $2 --speed 4 \
    --params $B/indi.params --out $O/$1_indi > $O/$1_indi.stdout 2>&1; echo "$1 seed$2 rc=$?" >> $B/done.txt
}
for seed in 1 2 3; do
  ( for s in step_roll step_pitch step_yaw torque_steps; do fly $s $seed; done ) &
done
wait
echo ALLDONE >> $B/done.txt
