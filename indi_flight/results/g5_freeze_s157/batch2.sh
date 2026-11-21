#!/usr/bin/env bash
# S157 freeze re-fly batch 2, serial (D-FREEZE-6): rows G5.5, G5.6/8/9/11 (events), G5.7, G5.10 + firmware-default cell.
# Same pattern as batch.sh: skips runs whose flight.ulg exists (resume = rerun), asserts MC_INDI_ID_OK. Repo root.
# Do NOT start while batch.sh is running (one serial stream). Checkers: checks.sh.
cd "$(dirname "$0")/../../.."
D=indi_flight/results/g5_freeze_s157; F=$D/fly.sh
# run <tag> <scenario> <seed> [runner args]; EXPECT = expected MC_INDI_ID_OK (default 1)
run() { local tag=$1; shift; [ -f $D/$tag/flight.ulg ] && return; TAGX=$TAGX bash $F "$@" >> $D/batch_status.txt 2>&1
  chk $tag; }
# runev <tag> <seed> [args]: G5 event injector (g5_events.py wraps run_scenario.main and forces --scenario g5_events); same plant as fly.sh
runev() { local tag=$1 seed=$2; shift 2; [ -f $D/$tag/flight.ulg ] && return
  docker ps -q --filter name=s157 | xargs -r docker stop >/dev/null
  timeout 1000 indi_project/docker/run.sh -n s157$tag -t 900 -- python3 indi_flight/bench/g5_events.py --controller indi \
    --model quad5in --seed $seed --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 \
    --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0 \
    --params $D/params.params "$@" --out $D/$tag > $D/$tag.stdout.log 2>&1
  echo "runev $tag rc=$?" >> $D/batch_status.txt; chk $tag; }
chk() { local tag=$1; python3 -c "import json,sys;r=json.load(open('$D/$tag/run.json'));v=r['params_applied'].get('MC_INDI_ID_OK');print('$tag ID_OK',v);sys.exit(str(v)!='${EXPECT:-1}')" >> $D/batch_status.txt 2>&1 || { echo "ABORT $tag ID_OK" >> $D/batch_status.txt; exit 1; }; }
for s in ${SEEDS:-1 2 3}; do
  # G5.5 offboard (bench/g55_check.py); scenarios from S139/S141 batches, no extra runner args
  for sc in offb_vel_step o1_lemniscate o2_circle_z o3_lemniscate_gust o4_lemniscate_payload o5_zsine_com_shift o6_zsine_mass o7_lemniscate_tau2; do
    TAGX= run ${sc}_s$s $sc $s
  done
  # G5.7 mode switch, posctl (bench/g57_check.py --validity leaveP)
  TAGX= run mode_switch10_s$s mode_switch10 $s --stick-mode posctl
  # G5.10 sustained saturation (bench/g510_check.py), freeze params.params == params_tb03 (TB 0.3)
  TAGX= run sat_sustained_s$s sat_sustained $s
  # G5.6/5.8(hover)/5.9/5.11 events, one hover flight per seed (bench/g5_rows_check.py); --moving NOT flown (G5.8 3 m/s cut)
  runev g5_events_s$s $s
  # firmware-default cell: G5.1 acro yaw at ID_OK 0 / W_MAX 0 / ACT_TC 0.05; later --params overrides fly.sh's (argparse last wins)
  EXPECT=0 TAGX=_fwdef_acro run stick_steps_s${s}_fwdef_acro stick_steps $s --stick-mode acro --stick-pilot --params $D/params_fwdef.params
done
echo DONE2 >> $D/batch_status.txt
