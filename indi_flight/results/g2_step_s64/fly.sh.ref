#!/usr/bin/env bash
# S64: G2-STEP first formal test (seeds 1-3, out results/g2_step_s64) + G4 pre-look, r_dot_f (rate_sp_dot) noise in hover and rate (acro-like) pulses, lead on vs off (MC_INDI_LEAD 0).
# quad5in, sim v2, 800 Hz, speed 4, seed 1. Run from the repo root.
B=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/stage3_s64
git rev-parse HEAD > $B/head.txt; git status --short | grep -v '^??' >> $B/head.txt
indi_project/docker/run.sh -n s64build -t 2400 -- make px4_sitl_default > $B/build.log 2>&1; echo "build rc=$?" >> $B/done.txt
fly() { # scenario params tag
  O=$B/$1_$3; mkdir -p $O
  indi_project/docker/run.sh -n s64_$1_$3 -t 900 -- python3 indi_flight/bench/run_scenario.py --scenario $1 \
    --controller indi --model quad5in --sim v2 --rate-hz 800 --seed 1 --speed 4 \
    --params $B/$2 --out $O/run > $O/stdout.txt 2>&1; echo "$1 $3 rc=$?" >> $B/done.txt
}
G=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/g2_step_s64
step() { # scenario seed  (G2-STEP first formal test, same command as stage3_s62/fly_steps.sh)
  O=$G/steps_seed$2; mkdir -p $O
  indi_project/docker/run.sh -n s64_$1_$2 -t 900 -- python3 indi_flight/bench/run_scenario.py --scenario $1 \
    --controller indi --model quad5in --sim v2 --rate-hz 800 --seed $2 --speed 4 \
    --params $G/indi.params --out $O/$1_indi > $O/$1_indi.stdout 2>&1; echo "$1 seed$2 rc=$?" >> $G/done.txt
}
grep -q "build rc=0" $B/done.txt || { echo "BUILD FAILED" >> $B/done.txt; exit 1; }
( for s in step_roll step_pitch step_yaw torque_steps; do step $s 1; done; fly hover indi.params lead1; fly rate_step_roll indi.params lead1 ) &
( for s in step_roll step_pitch step_yaw torque_steps; do step $s 2; done; fly hover indi_lead0.params lead0; fly rate_step_roll indi_lead0.params lead0 ) &
( for s in step_roll step_pitch step_yaw torque_steps; do step $s 3; done ) &
wait
echo ALLDONE >> $B/done.txt
