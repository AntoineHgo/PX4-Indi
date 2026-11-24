#!/usr/bin/env bash
# fly.sh NAME  (NAME = orig or a variant): INDI, draw index 24 only, speed 1, gate binary pinned.
set -u
N=$1; W=indi_flight/results/g3_refly_actc_s212/restore264
S=indi_flight/results/g3_refly_actc_s212/samples; [ "$N" = orig ] || S=$W/samples_$N
timeout 1500 bash indi_flight/bench/g3_chain.sh start $W/indi_$N 24 24 --samples $S --speed 1 \
  --allow-binary 903eae63ceb1bf019215076650cf02fb38cac8534618530410506f6a505f6d62 >$W/chain_start_$N.txt 2>&1
echo rc=$? >>$W/chain_start_$N.txt
