#!/usr/bin/env bash
# S161 G5.11 re-fly after D-T10-RESET (firmware 49568bcaa5): freeze plant/params, g5_events, seeds 1-3, serial. Repo root.
cd "$(dirname "$0")/../../.."
D=indi_flight/results/g511_fix_s161
timeout 1800 indi_project/docker/run.sh -n s161build "make px4_sitl_default" > $D/build.log 2>&1; echo "build rc=$?" >> $D/status.txt
for s in 1 2 3; do
  [ -f $D/g5_events_s$s/flight.ulg ] && continue
  docker ps -q --filter name=s161 | xargs -r docker stop >/dev/null
  timeout 1000 indi_project/docker/run.sh -n s161ev$s -t 900 -- python3 indi_flight/bench/g5_events.py --controller indi \
    --model quad5in --seed $s --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 \
    --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0 \
    --params $D/params.params --out $D/g5_events_s$s > $D/g5_events_s$s.stdout.log 2>&1
  echo "ev s$s rc=$?" >> $D/status.txt
done
echo DONE >> $D/status.txt
