#!/bin/bash
# PID control flight on the draw of run_<idx> (same command, --controller pid_default). Usage: ctl_pid.sh <idx>
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
R=indi_flight/results/g3_probe_s117; I=$(printf %03d $1)
CMD=$(python3 -c "
import json,sys
c=json.load(open('$R/run_$I/g3_draw.json'))['command']
c[c.index('--controller')+1]='pid_default'; c[c.index('--out')+1]='$R/ctl_pid_run$I'
c=[x.replace('/home/ahugo/Documents/Drotek/Codes/PX4-Indi/','') for x in c]; c[0]='python3'; print(' '.join(c))")
indi_project/docker/run.sh -n g3p117_pid$1 -t 1500 -- $CMD > $R/ctl_pid_run$I.txt 2>&1
echo "$(date +%H:%M:%S) pid$1 rc=$?" >> $R/progress.txt
