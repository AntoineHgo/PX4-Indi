#!/usr/bin/env bash
# S160 chain, serial, resumable, repo root: (1) wait for the G2 pre-test (roll 800/400 s1), (2) PID reference g5_events s1
# (F-5, G5.11 tilt-jump cause: stack-independent?), (3) remaining G2 freeze cells, (4) fwdef roll 800 cell.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi || exit 1
G=indi_flight/results/g2_freeze_s160; D=indi_flight/results/g5_freeze_s157
until grep -qE 'BATCH_DONE|ABORT' $G/batch.log; do timeout 20 tail -f /dev/null; done
grep -q ABORT $G/batch.log && { echo CHAIN_ABORT_PRETEST; exit 12; }
T=g5_events_s1_pid
[ -f $D/$T/flight.ulg ] || { docker ps -q --filter name=s157 | xargs -r docker stop >/dev/null
  timeout 1000 indi_project/docker/run.sh -n s157$T -t 900 -- python3 indi_flight/bench/g5_events.py --controller pid_default \
  --model quad5in --seed 1 --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0 \
  --out $D/$T > $D/$T.stdout.log 2>&1; echo "fly $T rc=$?"
  python3 indi_flight/bench/g511_check.py $D/$T > $D/$T.g511.txt 2>&1; }
CELLS="pitch:800:1 pitch:400:1 roll:800:2 roll:400:2 pitch:800:2 pitch:400:2 roll:800:3 roll:400:3 pitch:800:3 pitch:400:3" \
  bash $G/batch.sh >> $G/batch.log 2>&1
CELLS="roll:800:1 roll:800:2 roll:800:3" PSUF=_fwdef bash $G/batch.sh >> $G/batch.log 2>&1
echo CHAIN_END
