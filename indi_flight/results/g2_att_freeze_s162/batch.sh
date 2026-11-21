#!/usr/bin/env bash
# S162 G2 attitude cells at the stage-6 freeze (D-FREEZE-6 plant: matched GNSS 110, G4 typical noise).
# Recipe = g2_attbreak_s107/fly.sh (MC_INDI_INJ_PT 1 rate-setpoint break, RAMP 0.06, TP 10, 0.2-20 Hz, NP 5,
# hover_xlong, attitude_break_check.py + hole_report.py); base params = g2_freeze_s160/params_roll.params minus
# MC_INDI_INJ_* lines. CELLS="ax:hz:seed ..." (ax 1|2|3 roll|pitch|yaw). Serial, resumable, O-12 abort on early cells.
set -u
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi || exit 1
G=indi_flight/results/g2_att_freeze_s162
log() { echo "$(date +%H:%M:%S) $*"; }
docker ps -aq --filter "name=g2a" | xargs -r docker stop >/dev/null 2>&1
CELLS=${CELLS:-"1:800:1 3:800:1"}
idx=0
for cell in $CELLS; do
  IFS=: read -r ax hz seed <<< "$cell"
  N=ax${ax}_r${hz}_s${seed}
  if grep -q pm_deg "$G/${N}_margins.json" 2>/dev/null; then log "SKIP $N"; idx=$((idx+1)); continue; fi
  cp $G/params_base.params $G/$N.params
  printf 'MC_INDI_INJ_AX %s\nMC_INDI_INJ_PT 1\nMC_INDI_INJ_RAMP 0.06\nMC_INDI_INJ_TP 10\nMC_INDI_INJ_FMIN 0.2\nMC_INDI_INJ_FMAX 20\nMC_INDI_INJ_NP 5\nMC_INDI_INJ_DLY 20\n' "$ax" >> $G/$N.params
  log "START $N"
  indi_project/docker/run.sh -n g2a$N -t 1500 -- python3 indi_flight/bench/run_scenario.py --scenario hover_xlong \
    --controller indi --model quad5in --sim v2 --rate-hz $hz --seed $seed --speed 4 \
    --gps-dly 110 --gnss-delay 110 --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0 \
    --params $G/$N.params --out $G/$N > $G/$N.stdout.log 2>&1
  frc=$?
  indi_project/docker/run.sh -n g2ac$N -t 240 -- python3 indi_flight/bench/attitude_break_check.py $G/$N/flight.ulg $((ax-1)) \
    --Tp 10 --fmin 0.2 --fmax 20 > $G/${N}_check.txt 2>&1
  indi_project/docker/run.sh -n g2ah$N -t 240 -- python3 indi_flight/bench/hole_report.py $G/$N/flight.ulg > $G/${N}_holes.txt 2>&1
  indi_project/docker/run.sh -n g2am$N -t 240 -- python3 indi_flight/bench/ratesp_csv.py $G/$N/flight.ulg $((ax-1)) \
    $G/${N}_att.csv --Tp 10 --fmin 0.2 --fmax 20 --margins > $G/${N}_margins.json 2> $G/${N}_margins.err
  if grep -q pm_deg "$G/${N}_margins.json"; then log "DONE $N fly=$frc"; else
    log "NO_MARGINS $N fly=$frc"
    if [ $idx -lt 2 ]; then log "ABORT (O-12): early cell $N failed"; exit 12; fi
  fi
  idx=$((idx+1))
done
log "BATCH_END"
