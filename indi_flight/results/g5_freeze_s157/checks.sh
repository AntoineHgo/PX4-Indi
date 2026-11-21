#!/usr/bin/env bash
# S157 freeze: run every row checker on the freeze dirs, output to <name>.check.txt (repo root). Run after batch.sh/batch2.sh DONE.
# Host python3 if pyulog imports, else indi_project/docker/run.sh (as g5_g510_s151/fly.sh did for g510_check).
cd "$(dirname "$0")/../../.."
D=indi_flight/results/g5_freeze_s157; B=indi_flight/bench
if python3 -c "import pyulog" 2>/dev/null; then py() { python3 "$@"; }
else py() { indi_project/docker/run.sh -n s157chk -t 240 -- python3 "$@"; }; fi
c() { local name=$1; shift; [ -d $D/$name ] || { echo "skip $name (no dir)"; return; }; py "$@" > $D/$name.check.txt 2>&1; echo "$name rc=$?"; }
for s in ${SEEDS:-1 2 3}; do
  for m in acro stab; do c stick_steps_s${s}_$m $B/g51_check.py $D/stick_steps_s${s}_$m; done                 # G5.1
  for m in altctl posctl; do c stick_pos_steps_s${s}_$m $B/g52_check.py $D/stick_pos_steps_s${s}_$m; done      # G5.2
  [ -d $D/auto_tour_s$s ] && { py $B/g53_mission_check.py $D/auto_tour_s$s --json $D/auto_tour_s$s/g53.json > $D/auto_tour_s$s.g53.check.txt 2>&1; echo "g53 s$s rc=$?"; }   # G5.3
  for t in auto_tour_s$s auto_land10_s$s; do c $t $B/auto_smoke_check.py $D/$t --json $D/$t/check.json; done    # G5.4
  for sc in offb_vel_step o1_lemniscate o2_circle_z o3_lemniscate_gust o4_lemniscate_payload o5_zsine_com_shift o6_zsine_mass o7_lemniscate_tau2; do
    c ${sc}_s$s $B/g55_check.py $D/${sc}_s$s --json $D/${sc}_s$s/g55.json                                      # G5.5
  done
  c mode_switch10_s$s $B/g57_check.py --validity leaveP $D/mode_switch10_s$s                                    # G5.7
  c sat_sustained_s$s $B/g510_check.py $D/sat_sustained_s$s --json $D/sat_sustained_s$s/g510.json              # G5.10
  c g5_events_s$s $B/g5_rows_check.py $D/g5_events_s$s                                                          # G5.6/8/9/11
  c stick_steps_s${s}_fwdef_acro $B/g51_check.py $D/stick_steps_s${s}_fwdef_acro                                # firmware-default cell
done
