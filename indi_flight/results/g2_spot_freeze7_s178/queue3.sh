#!/usr/bin/env bash
# Freeze-7 G2 spot-check (2 cells), chained after g2_outer_freeze7_s177/queue2.sh. Serial, idempotent; resume = rerun.
cd "$(dirname "$0")/../../.." || exit 1
D=indi_flight/results/g2_spot_freeze7_s178; Q2=indi_flight/results/g2_outer_freeze7_s177
S=$D/queue3_status.tsv
ready() { grep -q '^end ' $Q2/queue2.log 2>/dev/null && grep -q QUEUE_END $Q2/queue2.log \
  && [ "$(ls $Q2/*_margins.json 2>/dev/null | while read f; do [ -s $f ] && echo $f; done | wc -l)" -ge 24 ] \
  && [ -z "$(docker ps -q --filter name=s177)" ] && [ -z "$(docker ps -q --filter name=s178s)" ]; }
echo "wait for queue2 end (24 margins, no s177* container) $(date '+%F %T')"
for i in $(seq 360); do ready && break; sleep 30; done   # 360 x 30 s = 3 h
ready || { echo WAIT_TIMEOUT; echo QUEUE3_END; exit 2; }
echo "start $(date '+%F %T')"
[ -f $S ] || printf 'cell\tstart\tend\trc\n' > $S
for c in rate att; do t0=$(date '+%F %T'); bash $D/fly.sh $c; rc=$?
  printf '%s\t%s\t%s\t%s\n' $c "$t0" "$(date '+%F %T')" $rc >> $S; done
echo "end $(date '+%F %T')"; echo QUEUE3_END
