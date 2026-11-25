#!/bin/bash
# S227 PID reference: fly (fly_pid_s227.py), then score with key 1 (g3_score.sh, as the chain does) and key 2 (g3_checks_key2.py)
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi || exit 1
P=indi_flight/results/g3_pretest_s227/pid_ref
python3 $P/fly_pid_s227.py > $P/fly.log 2>&1 || { echo "FLY_FAILED" >> $P/fly.log; exit 1; }
mkdir -p $P/.score_tmp
ln -sfn ../run_000 $P/.score_tmp/run_000
indi_project/docker/run.sh -n g3pidS227k1 -t 900 -- bash indi_flight/bench/g3_score.sh $P/.score_tmp > $P/chain_key1.txt 2>&1
args=$(grep -E "^run_000 --run-json " $P/chain_key1.txt | head -1 | cut -d' ' -f2- | sed 's#/.score_tmp/run_000/#/run_000/#')
echo "ARGS $args" >> $P/fly.log
unlink $P/.score_tmp/run_000
rmdir $P/.score_tmp
if [ -n "$args" ]; then
  mkdir -p $P/key2
  # shellcheck disable=SC2086
  indi_project/docker/run.sh -n g3pidS227k2 -t 500 -- python3 indi_flight/bench/g3_checks_key2.py $P/run_000 $args --out $P/key2 > $P/chain_key2.txt 2>&1
else
  echo "no key-1 argument line" > $P/chain_key2.txt
fi
echo PIPELINE_DONE >> $P/fly.log
