#!/usr/bin/env bash
# T153 (a30_seq_s69): A-30 closing test. Command of results/g16_sched_indi_s68/fly.sh (INDI, step_roll, sim v2,
# 400 Hz, seed 1, speed 4, --sched --sched-anchor, params g2_step_s64_400/indi.params), but 5 runs STRICTLY SEQUENTIAL
# (S68 ran them up to 5 in parallel). A-32 (results/a32_load_s69) showed the PID spread comes from parallel host load.
G=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/a30_seq_s69
P400=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/g2_step_s64_400/indi.params
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi || exit 1
for r in r1 r2 r3 r4 r5; do
  d=$G/seq/$r; mkdir -p $d; t0=$(date +%s)
  indi_project/docker/run.sh -n s69a_$r -t 900 -- python3 indi_flight/bench/run_scenario.py --scenario step_roll \
    --controller indi --model quad5in --sim v2 --rate-hz 400 --seed 1 --speed 4 --sched --sched-anchor \
    --params $P400 --out $d > $d/stdout.txt 2>&1
  echo "$r rc=$? wall=$(( $(date +%s) - t0 ))s" >> $G/done.txt
done
echo ALLDONE >> $G/done.txt
