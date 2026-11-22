#!/usr/bin/env bash
# flies the G5 gap flights serially (S198); same command as queue.sh ev()
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi || exit 1
G=indi_flight/results/freeze10_s193/g5_gaps_s198; P=indi_flight/results/g5_freeze_s157/params.params; B=indi_flight/bench
PLANT="--model quad5in --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0"
fl() { local name=$1 o=$2; shift 2
  docker ps -q | xargs -r docker stop >/dev/null 2>&1
  echo "$(date '+%F %T') start $name" >> $G/progress.txt
  timeout 1000 indi_project/docker/run.sh -n s198g5_$name -t 900 -- python3 $B/g5_events.py --controller indi $PLANT --seed $1 --params $P "${@:2}" --out $o > $o.stdout.log 2>&1
  echo "$(date '+%F %T') end $name rc=$?" >> $G/progress.txt; }
fl2() { local name=$1 sd=$2 o=$3; shift 3
  docker ps -q | xargs -r docker stop >/dev/null 2>&1
  echo "$(date '+%F %T') start $name" >> $G/progress.txt
  timeout 1000 indi_project/docker/run.sh -n s198g5_$name -t 900 -- python3 $B/g5_events.py --controller indi $PLANT --seed $sd --params $P "$@" --out $o > $o.stdout.log 2>&1
  echo "$(date '+%F %T') end $name rc=$?" >> $G/progress.txt; }
for s in 2 3; do fl2 ev_s$s $s $G/events/g5_events_s$s; done
for s in 1 2 3; do fl2 mov_s$s $s $G/moving/g5_events_mov_s$s --moving; done
echo ALLDONE >> $G/progress.txt
