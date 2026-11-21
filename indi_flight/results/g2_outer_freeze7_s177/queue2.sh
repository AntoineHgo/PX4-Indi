#!/usr/bin/env bash
# Freeze-7 re-fly of the 24 G2 outer cells (same cells/commands as g2_outer_freeze_s163/batch.sh, fly.sh out dir changed).
# Serial, idempotent: a cell with flight.ulg is not re-flown (only scored if margins json is empty). Resume = rerun.
cd "$(dirname "$0")/../../.." || exit 1
D=indi_flight/results/g2_outer_freeze7_s177; Q=indi_flight/results/freeze7_s177
S=$D/queue2_status.tsv
echo "wait for $Q/queue.log QUEUE_END $(date '+%F %T')"
for i in $(seq 240); do   # 240 x 30 s = 2 h
  if grep -q QUEUE_END $Q/queue.log 2>/dev/null && [ -z "$(docker ps -q --filter name=s177)" ]; then break; fi
  sleep 30
done
if ! { grep -q QUEUE_END $Q/queue.log 2>/dev/null && [ -z "$(docker ps -q --filter name=s177)" ]; }; then echo WAIT_TIMEOUT; echo QUEUE_END; exit 2; fi
echo "start $(date '+%F %T')"
[ -f $S ] || printf 'cell\tstart\tend\trc\tflight_ulg\n' > $S
run() { N=pt$1_ax$2_r$3_s$4
  [ -f $D/$N/flight.ulg ] && [ -s $D/${N}_margins.json ] && return
  local t0; t0=$(date '+%F %T'); bash $D/fly.sh "$@"; local rc=$?
  printf '%s\t%s\t%s\t%s\t%s\n' $N "$t0" "$(date '+%F %T')" $rc "$([ -f $D/$N/flight.ulg ] && echo yes || echo no)" >> $S; }
for c in "1 3 800 1" "0 3 800 1" "1 3 400 1" "0 3 400 1" "1 3 800 2" "0 3 800 2" "1 3 400 2" "0 3 400 2"; do run $c; done
export AMP=0.08 TP=20 SCN=hover_xlong
for s in 1 2; do for r in 800 400; do for ax in 1 2; do for pt in 1 0; do run $pt $ax $r $s; done; done; done; done
echo "end $(date '+%F %T')"; echo QUEUE_END
