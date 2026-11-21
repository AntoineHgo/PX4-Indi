#!/usr/bin/env bash
# S157 freeze re-fly batch, serial (D-FREEZE-6). Skips runs whose flight.ulg exists: resume = rerun. Repo root.
# Rows: G5.1 stick_steps acro/stabilized (--stick-pilot), G5.2 stick_pos_steps altctl/posctl, G5.3 mission + G5.4 auto_tour/auto_land10.
cd "$(dirname "$0")/../../.."
D=indi_flight/results/g5_freeze_s157; F=$D/fly.sh
run() { local tag=$1; shift; [ -f $D/$tag/flight.ulg ] && return; TAGX=$TAGX bash $F "$@" >> $D/batch_status.txt 2>&1
  python3 -c "import json,sys;r=json.load(open('$D/$tag/run.json'));v=r['params_applied'].get('MC_INDI_ID_OK');print('$tag ID_OK',v);sys.exit(str(v)!='1')" >> $D/batch_status.txt 2>&1 || { echo "ABORT $tag ID_OK" >> $D/batch_status.txt; exit 1; }; }
for s in ${SEEDS:-1 2 3}; do
  TAGX=_acro run stick_steps_s${s}_acro stick_steps $s --stick-mode acro --stick-pilot
  TAGX=_stab run stick_steps_s${s}_stab stick_steps $s --stick-mode stabilized --stick-pilot
  TAGX=_altctl run stick_pos_steps_s${s}_altctl stick_pos_steps $s --stick-mode altctl
  TAGX=_posctl run stick_pos_steps_s${s}_posctl stick_pos_steps $s --stick-mode posctl
  TAGX= run auto_tour_s$s auto_tour $s
  TAGX= run auto_land10_s$s auto_land10 $s
done
echo DONE >> $D/batch_status.txt
