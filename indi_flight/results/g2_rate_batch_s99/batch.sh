#!/usr/bin/env bash
# S99 G2 rate-loop margin batch: 10 cells, serial, resumable (skips cells whose margins.txt exists).
# Recipe = g2_rate_pretest_s99/fly.sh; params per axis (only MC_INDI_INJ_AX differs); rate via --rate-hz; seed via --seed.
set -u
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi || exit 1
G=indi_flight/results/g2_rate_batch_s99
log() { echo "$(date +%H:%M:%S) $*"; }

# stop stray batch containers before starting
docker ps -aq --filter "name=px4-indi-g2" | xargs -r docker stop >/dev/null 2>&1

declare -A AXIS_CSV=([roll]=0 [pitch]=1 [yaw]=2)
CELLS="roll:800:1 roll:800:2 roll:400:1 roll:400:2 pitch:800:2 pitch:400:1 pitch:400:2 yaw:800:1 yaw:800:2 yaw:400:2"

idx=0
for cell in $CELLS; do
  IFS=: read -r ax hz seed <<< "$cell"
  name=${ax}${hz}_s${seed}
  D=$G/$name
  P=$G/params_${ax}.params
  mkdir -p "$D"
  if [ -s "$D/margins.txt" ]; then
    log "SKIP $name (margins exists)"; idx=$((idx+1)); continue
  fi
  log "START $name"
  indi_project/docker/run.sh -n g2b_$name -t 900 -- python3 indi_flight/bench/run_scenario.py --scenario hover_long --controller indi_m3a \
    --seed $seed --speed 4 --model quad5in --rate-hz $hz --sim v2 --params $P --out $D/s1 > $D/stdout.log 2>&1
  frc=$?
  echo "fly rc=$frc" >> $D/done.txt
  indi_project/docker/run.sh -n g2c_$name -t 600 -- bash -c "python3 indi_flight/bench/check_rates.py $D/s1 > $D/rates.txt 2>&1; \
    python3 indi_flight/bench/pretest_gate.py $D/s1/flight.ulg $D/gate.md --delay 4 --length 15 > $D/gate_stdout.txt 2>&1; \
    python3 indi_flight/bench/m3a_csv.py $D/s1/flight.ulg ${AXIS_CSV[$ax]} $D/s1.csv > $D/csv_stdout.txt 2>&1; \
    python3 indi_flight/bench/m3a_margins_pretest.py $D/s1.csv 1 60 10 $hz > $D/margins.txt 2>&1" > $D/post.log 2>&1
  prc=$?
  echo "post rc=$prc" >> $D/done.txt
  if [ -s "$D/margins.txt" ]; then
    log "DONE $name fly=$frc post=$prc margins=ok"
  else
    log "NO_MARGINS $name fly=$frc post=$prc"
    if [ $idx -lt 2 ]; then log "ABORT (O-12): early cell $name failed"; exit 12; fi
  fi
  idx=$((idx+1))
done
log BATCH_DONE
