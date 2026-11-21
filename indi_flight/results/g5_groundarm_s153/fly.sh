#!/usr/bin/env bash
# S153 ground-arm probe (arm on the ground in altctl / posctl, low then centre throttle, climb to 3 m). Repo root.
# usage: fly.sh [indi_altctl indi_posctl pid_altctl]   (default: all three, serial)
D=indi_flight/results/g5_groundarm_s153
COMMON="--model quad5in --seed 1 --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 --scenario stick_ground_arm"
P=indi_flight/results/g5_g510_s150/params_tb03.params
docker ps -q --filter name=s153 | xargs -r docker stop
for RUN in ${@:-indi_altctl indi_posctl pid_altctl}; do
  MODE=${RUN#*_}; CTL=${RUN%%_*}
  if [ $CTL = indi ]; then X="--controller indi --params $P"; else X="--controller pid_default"; fi
  indi_project/docker/run.sh -n s153$RUN -t 600 -- python3 indi_flight/bench/run_scenario.py $X $COMMON \
    --stick-mode $MODE --ground-arm --out $D/$RUN > $D/$RUN.stdout.log 2>&1
  indi_project/docker/run.sh -n s153c$RUN -t 240 -- python3 indi_flight/bench/groundarm_check.py $D/$RUN \
    --json $D/$RUN/check.json > $D/$RUN.check.txt 2>&1
done
echo "groundarm done"
