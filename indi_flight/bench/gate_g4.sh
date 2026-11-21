#!/bin/sh
# G4 noise and effort gate (GATES section 4). Run from the repo root.
#   gate_g4.sh fly   OUT [profile flight seed]   fly one run, or all 18 (3 profiles x hover/cruise x 3 seeds), serial
#   gate_g4.sh score OUT                          score every run dir in OUT with bench/g4_metrics.py -> OUT/g4_table.md
#     (score needs pyulog/scipy: run it in Docker, indi_project/docker/run.sh -n g4score -t 900 -- sh <this> score OUT)
# Acro row: not yet flown (stick quantisation model deferred, RC168).
# Config: freeze params (D-FREEZE-6), matched GNSS 110 ms, SIM_GZ_ESC_FB=2 default of the runner, profiles D-NOISE-PROF.
set -u
P=indi_flight/results/g5_freeze_s157/params.params
MODE=$1; O=$2; shift 2
prof_args() {
  case $1 in
    quiet) echo "--vib-acc 0.5 --vib-gyr 0 --imu-noise-scale 1.0" ;;
    typ)   echo "--vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0" ;;
    harsh) echo "--vib-acc 27 --vib-gyr 0 --imu-noise-scale 4.0" ;;
  esac
}
scen() { [ "$1" = hover ] && echo hover_long || echo traj_lemniscate; }
fly1() {
  pr=$1; fl=$2; sd=$3; n=${fl}_${pr}_s${sd}
  [ -f "$O/$n/flight.ulg" ] && { echo "$n skip (exists)" >> "$O/status.txt"; return; }
  timeout 900 indi_project/docker/run.sh -n g4$n -t 900 -- python3 indi_flight/bench/run_scenario.py \
    --controller indi --model quad5in --seed "$sd" --speed 4 --sim v2 --params $P --gps-dly 110 --gnss-delay 110 \
    --scenario "$(scen "$fl")" $(prof_args "$pr") --out "$O/$n" > "$O/$n.log" 2>&1
  echo "$n rc $?" >> "$O/status.txt"
}
if [ "$MODE" = fly ]; then
  mkdir -p "$O"
  if [ $# -eq 3 ]; then fly1 "$1" "$2" "$3"; exit; fi
  for sd in 1 2 3; do for pr in quiet typ harsh; do for fl in hover cruise; do fly1 $pr $fl $sd; done; done; done
  touch "$O/CHAIN_END"; exit
fi
# score: window = hold event + 5 s .. end (hover), traj event + 3 s ramp .. end (cruise); log time base.
echo "| run | window (s) | truth | R20 % hover | R4 % | C20 | C4 | clip |" > "$O/g4_table.md"
echo "|---|---|---|---|---|---|---|---|" >> "$O/g4_table.md"
for d in "$O"/*_s[0-9]; do
  n=$(basename "$d"); [ -f "$d/flight.ulg" ] || { echo "| $n | NO LOG | | | | | | |" >> "$O/g4_table.md"; continue; }
  case $n in hover_*) ev=hold; sk=5 ;; *) ev=traj; sk=3 ;; esac
  w=$(python3 -c "
import json; from pyulog import ULog
u=ULog('$d/flight.ulg',['vehicle_status']); s=u.start_timestamp
e=[e for e in json.load(open('$d/run.json'))['events'] if e['name']=='$ev'][0]
t=(e['t_us']-s)*1e-6; print('%.2f %.2f'%(t+$sk, t+e['dur_s']))")
  set -- $w
  python3 indi_flight/bench/g4_metrics.py "$d/flight.ulg" --t0 "$1" --t1 "$2" --json "$d/g4_metrics.json" > /dev/null
  python3 -c "
import json; d=json.load(open('$d/g4_metrics.json'))
m=lambda k: d[k]['mean'] if 'mean' in d[k] else sum(d[k]['per_motor'])/4
print('| $n | $1-$2 | %s | %.3f | %.3f | %.5f | %.5f | %.4f |' % (d['rotor_speed_is_truth'], d['R20']['mean_pct_hover'], d['R4']['mean_pct_hover'], m('C20'), m('C4'), d['clip_fraction']))" >> "$O/g4_table.md"
done
