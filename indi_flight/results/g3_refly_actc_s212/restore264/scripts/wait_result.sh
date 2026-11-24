#!/usr/bin/env bash
# wait_result.sh NAME: wait (max 20 min) for the chain dir to finish, then print the run verdict and max truth tilt.
D=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/g3_refly_actc_s212/restore264/indi_$1
for i in $(seq 240); do [ -e $D/CHAIN_FINISHED ] || [ -e $D/CHAIN_HALTED ] || [ -e $D/CHAIN_FAILED ] && break; sleep 5; done
ls $D | tr '\n' ' '; echo
python3 -I - $D <<'P'
import json,sys,glob
d=sys.argv[1]+'/run_024/'
for f in ('g3_done.json','run.json'):
    try: j=json.load(open(d+f))
    except Exception as e: print(f,e); continue
    print(f,json.dumps({k:j.get(k) for k in ('outcome','exit_status','error','watchdog','g3_outcome','metrics_status')})[:600])
P
cat $D/SCORES.tsv 2>/dev/null | head -5
