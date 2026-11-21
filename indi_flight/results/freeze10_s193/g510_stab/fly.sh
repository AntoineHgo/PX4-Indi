#!/usr/bin/env bash
# usage: fly.sh <indi|pid> <seed>   (G5.10 stabilized full-scale part, scenario g510_stab_full, freeze-9 config)
cd "$(dirname "$0")/../../../.." || exit 1
R=indi_flight/results/freeze10_s193/g510_stab; P=indi_flight/results/g5_freeze_s157/params.params
c=$1; s=$2; o=$R/${c}_stab_s$s
X=; [ $c = indi ] && X="--params $P"
docker ps -q --filter name=s193stab | xargs -r docker stop >/dev/null
timeout 1000 indi_project/docker/run.sh -n s193stab${c}_s$s -t 900 -- python3 indi_flight/bench/run_scenario.py --controller $c $X \
  --model quad5in --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0 \
  --seed $s --scenario g510_stab_full --stick-mode stabilized --out $o > $o.stdout.log 2>&1
echo "rc=$?"
python3 indi_flight/bench/g510_score_motors.py $o --json $o/score_key1.json > $o.score_key1.txt 2>&1; cat $o.score_key1.txt
python3 indi_flight/bench/g510_motors_key2.py $o > $o.score_key2.txt 2>&1; cat $o.score_key2.txt
