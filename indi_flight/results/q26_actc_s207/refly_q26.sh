#!/bin/bash
# Q26 check: INDI speed 1, 8 S199 re-fly draws, set a (ACT_TC = tau_slow) then set b (1.5 x tau_slow). Serial, resumable.
# Usage (any cwd): setsid nohup bash indi_flight/results/q26_actc_s207/refly_q26.sh >/dev/null 2>&1 </dev/null &
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi || exit 1
W=indi_flight/results/q26_actc_s207
CH=indi_flight/bench/g3_chain.sh
IDXS="245 264 008 240 283 239 046 039"
INDI_WALL=3300   # s, as in refly_all.sh
log() { echo "$(date '+%F %T') $*" >> $W/progress.txt; }
log "BATCH_START pid=$$ indices: $IDXS sets: a b"
for set in a b; do
for i in $IDXS; do
  n=$(printf %03d $((10#$i)))
  D=$W/${set}_$n
  tag="set=$set idx=$n"
  if [ -f $D/CHAIN_FINISHED ]; then log "$tag skip (finished)"; continue; fi
  if [ -f $D/CHAIN_HALTED ]; then log "$tag HALTED earlier, skip (diagnose, rm CHAIN_HALTED to retry)"; continue; fi
  log "$tag start params=${set}_$n"
  for w in $(seq 1 360); do flock -n indi_flight/logs/flight_chain.lock true && break; sleep 10; done
  G3_PARAMS=$W/params/${set}_$n.params bash $CH start $D $((10#$i)) $((10#$i)) --speed 1 >> $W/chain_start_${set}_$n.txt 2>&1
  t0=$(date +%s)
  while [ ! -f $D/CHAIN_FINISHED ] && [ ! -f $D/CHAIN_HALTED ]; do
    sleep 15
    if [ $(( $(date +%s) - t0 )) -gt $INDI_WALL ]; then
      log "$tag WALL TIMEOUT, stop --now"; bash $CH stop $D --now >> $W/chain_start_${set}_$n.txt 2>&1; break
    fi
    if [ $(( $(date +%s) - t0 )) -gt 60 ] && flock -n indi_flight/logs/flight_chain.lock true; then
      [ -f $D/CHAIN_FINISHED ] || [ -f $D/CHAIN_HALTED ] || { log "$tag chain gone without marker"; break; }
    fi
  done
  for m in CHAIN_FINISHED CHAIN_HALTED; do [ -f $D/$m ] && log "$tag $m"; done
  log "$tag end $(bash $CH status $D 2>&1 | sed -n 2,3p | tr '\n' ' ')"
done
done
log "BATCH_END"
touch $W/DONE
