#!/bin/bash
# G3 S199 re-fly batch: per index, INDI at speed 1 (g3_chain.sh, own dir) then PID at speed 1. Serial, resumable. See README.md.
# Usage (any cwd): setsid nohup bash indi_flight/results/g3_refly_s199/refly_all.sh >/dev/null 2>&1 </dev/null &
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi || exit 1
W=indi_flight/results/g3_refly_s199
CH=indi_flight/bench/g3_chain.sh
IDXS="245 264 008 240 283 239 046 039"
INDI_WALL=3300   # s: chain start to CHAIN_FINISHED (flight <=1700 x 2 attempts is capped by this; scoring included)
PID_WALL=1700    # s: PID flight
log() { echo "$(date '+%F %T') $*" >> $W/progress.txt; }
log "BATCH_START pid=$$ indices: $IDXS"
for i in $IDXS; do
  n=$(printf %03d $((10#$i)))
  # ---- INDI speed 1
  D=$W/indi_$n
  if [ -f $D/CHAIN_FINISHED ]; then log "idx=$n INDI skip (finished)"; else
    log "idx=$n INDI start"
    # wait for any other chain (lock) to end, at most 1 h
    for w in $(seq 1 360); do flock -n indi_flight/logs/flight_chain.lock true && break; sleep 10; done
    bash $CH start $D $((10#$i)) $((10#$i)) --speed 1 >> $W/chain_start_$n.txt 2>&1
    t0=$(date +%s)
    while [ ! -f $D/CHAIN_FINISHED ] && [ ! -f $D/CHAIN_HALTED ]; do
      sleep 15
      if [ $(( $(date +%s) - t0 )) -gt $INDI_WALL ]; then
        log "idx=$n INDI WALL TIMEOUT, stop --now"; bash $CH stop $D --now >> $W/chain_start_$n.txt 2>&1; break
      fi
      # chain died without a marker (lock free, no marker): give up on this index
      if [ $(( $(date +%s) - t0 )) -gt 60 ] && flock -n indi_flight/logs/flight_chain.lock true; then
        [ -f $D/CHAIN_FINISHED ] || [ -f $D/CHAIN_HALTED ] || { log "idx=$n INDI chain gone without marker"; break; }
      fi
    done
    for m in CHAIN_FINISHED CHAIN_HALTED; do [ -f $D/$m ] && log "idx=$n INDI $m"; done
    log "idx=$n INDI end $(bash $CH status $D 2>&1 | sed -n 2,3p | tr '\n' ' ')"
  fi
  # ---- PID speed 1
  P=$W/pid_$n
  if [ -f $P/DONE ]; then log "idx=$n PID skip (done)"; continue; fi
  mkdir -p $P
  if [ -d $P/run_$n ] && [ ! -f $P/run_$n/g3_done.json ]; then mv $P/run_$n $P/run_$n.incomplete_$(date +%H%M%S); fi
  docker ps -q --filter "name=g3pid199_" | xargs -r docker stop >/dev/null 2>&1
  if [ ! -f $P/run_$n/g3_done.json ]; then
    log "idx=$n PID start"
    timeout $PID_WALL python3 $W/fly_pid_run.py $((10#$i)) > $P/stream.txt 2>&1
    log "idx=$n PID flight rc=$?"
  fi
  if [ -f $P/run_$n/g3_done.json ]; then
    mkdir -p $P/key2
    timeout 1000 bash indi_flight/bench/g3_score_docker.sh $P > $P/SCORE_KEY1.txt 2>&1
    grep -E '^run_[0-9]+ --t0' $P/SCORE_KEY1.txt | while read -r run args; do
      # shellcheck disable=SC2086
      timeout 600 indi_project/docker/run.sh -n g3pid199_k2 -t 500 -- python3 indi_flight/bench/g3_checks_key2.py $P/$run $args --out $P/key2 > $P/SCORE_KEY2.txt 2>&1
    done
    log "idx=$n PID scored (key1 $(ls $P/run_$n/g3_checks.json 2>/dev/null | wc -l), key2 $(ls $P/key2/*.json 2>/dev/null | wc -l) files)"
    touch $P/DONE
  else
    log "idx=$n PID FAILED (no g3_done.json), see $P/stream.txt"
  fi
done
log "BATCH_END"
touch $W/DONE
