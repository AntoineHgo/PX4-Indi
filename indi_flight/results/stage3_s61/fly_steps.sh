#!/usr/bin/env bash
# S61 (owner note N1 item B.1): INDI vs PID attitude steps + torque steps, seeds 2 and 3, gate-bearing provenance
# (clean tree, binary built at HEAD d7c637cb20). Same command as results/indi_vs_pid/fly.sh except seed and --out.
# Run from the repo root.
B=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/stage3_s61
fly() { # scenario controller seed
  O=$B/steps_seed$3; mkdir -p $O
  indi_project/docker/run.sh -n s61_$1_$2_$3 -t 900 -- python3 indi_flight/bench/run_scenario.py --scenario $1 \
    --controller $2 --model quad5in --sim v2 --rate-hz 800 --seed $3 --speed 4 \
    --params $B/$2.params --out $O/$1_$2 > $O/$1_$2.stdout 2>&1; echo "$1 $2 seed$3 rc=$?" >> $B/done.txt
}
for c in indi pid; do for grp in "step_roll step_pitch" "step_yaw torque_steps"; do
  ( for seed in 2 3; do for s in $grp; do fly $s $c $seed; done; done ) &
done; done
wait
echo ALLDONE >> $B/done.txt
