#!/bin/bash
# S118 pre-test of D-G3-STICK-PILOT (--stick-pilot, wired by g3_run for stabilized/acro): re-fly the S117 probe
# draws idx 0 (acro), 21, 49 (stabilized) with INDI, then the same draws with PID (control). Probe, not gate evidence.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
R=indi_flight/results/g3_pilot_s118
one() {
  i=$1
  indi_project/docker/run.sh -n g3p118_$i -t 1500 -- python3 indi_flight/bench/g3_run.py --seed 117 --n 60 \
    --start $i --stop $i --base-params indi_flight/bench/params/quad5in_indi_g1.params \
    --out-root $R --timeout-s 1200 > $R/stream_$i.txt 2>&1
  echo "$(date +%H:%M:%S) idx=$i docker_rc=$?" >> $R/progress.txt
  I=$(printf %03d $i)
  CMD=$(python3 -c "
import json
c=json.load(open('$R/run_$I/g3_draw.json'))['command']
c[c.index('--controller')+1]='pid_default'; c[c.index('--out')+1]='$R/pid_run$I'
c=[x.replace('/home/ahugo/Documents/Drotek/Codes/PX4-Indi/','') for x in c]; c[0]='python3'; print(' '.join(c))")
  indi_project/docker/run.sh -n g3p118_pid$i -t 1500 -- $CMD > $R/pid_run$I.txt 2>&1
  echo "$(date +%H:%M:%S) pid$i rc=$?" >> $R/progress.txt
}
export -f one; export R
printf '%s\n' 0 21 49 | xargs -P 3 -I{} bash -c 'one {}'
echo "$(date +%H:%M:%S) BATCH_END" >> $R/progress.txt
