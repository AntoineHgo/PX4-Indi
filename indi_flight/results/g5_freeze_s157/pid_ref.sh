#!/usr/bin/env bash
# S158 Q10 PID reference (F-5): stick_pos_steps posctl seed 1, same plant/noise as the freeze, stock PID, no params
# file (a params file with MC_INDI_EN 1 would fly INDI, STATE runner trap). Serial: waits for CHAIN_END. Repo root.
cd "$(dirname "$0")/../../.."
D=indi_flight/results/g5_freeze_s157; T=stick_pos_steps_s1_posctl_pid
until grep -q CHAIN_END $D/batch_status.txt; do sleep 60; done
[ -f $D/$T/flight.ulg ] && exit 0
docker ps -q --filter name=s157 | xargs -r docker stop >/dev/null
timeout 1000 indi_project/docker/run.sh -n s157$T -t 900 -- python3 indi_flight/bench/run_scenario.py --controller pid_default \
  --model quad5in --seed 1 --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 \
  --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0 \
  --scenario stick_pos_steps --stick-mode posctl --out $D/$T > $D/$T.stdout.log 2>&1
echo "fly $T rc=$?" >> $D/batch_status.txt
python3 indi_flight/bench/g52_check.py $D/$T > $D/$T.check.txt 2>&1; echo "PID_REF_END" >> $D/batch_status.txt
