#!/usr/bin/env bash
# Freeze-9 gate re-fly queue (D-FREEZE-9, S183), serial and idempotent. Resume = rerun this script from anywhere.
# Order: G2 outer 24 + spot 2, G4 18, G5.5 24, G5.3/G5.4 (auto_tour, auto_land10, hold_wind x3 = 9), events 1, G2-STEP 3 seeds x 3.
# An item is skipped when its done-file exists (flight.ulg, or margins output for G2 cells).
# Params: results/g5_freeze_s157/params.params, no MC_INDI_XY_P/XY_VP (firmware defaults 1.2/2.4).
cd "$(dirname "$0")/../../.." || exit 1
R=indi_flight/results/freeze9_s183; P=indi_flight/results/g5_freeze_s157/params.params
HW=indi_flight/results/g5_freeze_s157/hold_wind_overrides.json
S=$R/queue_status.tsv; mkdir -p $R/g2o $R/g2s $R/g55 $R/g4 $R/g5 $R/events $R/steps
[ -f $S ] || printf 'name\tstart\tend\trc\n' > $S
stamp() { date '+%F %T'; }
item() { # item <name> <donefile> <cmd...>
  local n=$1 o=$2; shift 2
  [ -s $o ] && return
  docker ps -q --filter name=s183f9 | xargs -r docker stop >/dev/null
  local t0; t0=$(stamp); "$@"; local rc=$?
  printf '%s\t%s\t%s\t%s\n' "$n" "$t0" "$(stamp)" $rc >> $S
}
PLANT="--model quad5in --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0"
fly() { # fly <group> <scenario> <seed> [extra runner args]
  local g=$1 sc=$2 sd=$3 o=$R/$1/${2}_s$3; shift 3
  timeout 1000 indi_project/docker/run.sh -n s183f9${sc}_s$sd -t 900 -- python3 indi_flight/bench/run_scenario.py --controller indi \
    $PLANT --seed $sd --params $P --scenario $sc "$@" --out $o > $o.stdout.log 2>&1
}
g2o() { timeout 1500 bash $R/g2o_fly.sh "$@"; }
g2s() { timeout 2000 bash $R/g2s_fly.sh "$@"; }
g4() { timeout 1000 sh indi_flight/bench/gate_g4.sh fly $R/g4 "$1" "$2" "$3"; }
ev() { local o=$R/events/g5_events_s$1
  timeout 1000 indi_project/docker/run.sh -n s183f9g5_events_s$1 -t 900 -- python3 indi_flight/bench/g5_events.py --controller indi \
    $PLANT --seed $1 --params $P --out $o > $o.stdout.log 2>&1; }
step() { local sd=$1 sc=$2
  timeout 900 indi_project/docker/run.sh -n s183f9_${sc}_s$sd -t 900 -- python3 indi_flight/bench/run_scenario.py --scenario $sc --controller indi \
    --model quad5in --sim v2 --rate-hz 800 --seed $sd --speed 4 --params indi_flight/results/g2_step_s64/indi.params \
    --out $R/steps/seed$sd/${sc}_indi > $R/steps/seed${sd}_$sc.stdout 2>&1; }
# 1. G2 outer cells (queue2.sh of g2_outer_freeze7_s177) then 2 spot cells
for c in "1 3 800 1" "0 3 800 1" "1 3 400 1" "0 3 400 1" "1 3 800 2" "0 3 800 2" "1 3 400 2" "0 3 400 2"; do
  set -- $c; item g2o_pt$1_ax$2_r$3_s$4 $R/g2o/pt$1_ax$2_r$3_s$4_margins.json g2o $c; done
for s in 1 2; do for r in 800 400; do for ax in 1 2; do for pt in 1 0; do
  item g2o_pt${pt}_ax${ax}_r${r}_s$s $R/g2o/pt${pt}_ax${ax}_r${r}_s${s}_margins.json env AMP=0.08 TP=20 SCN=hover_xlong bash -c "timeout 1500 bash $R/g2o_fly.sh $pt $ax $r $s"
done; done; done; done
item g2s_rate $R/g2s/roll800_fwdef_s2/margins.txt g2s rate
item g2s_att $R/g2s/ax2_r400_s1_margins.json g2s att
# 3. G4
for sd in 1 2 3; do for pr in quiet typ harsh; do for fl in hover cruise; do
  # cruise_harsh_s2 was held for Q19 (closed S183), flown in the rerun
  item g4_${fl}_${pr}_s$sd $R/g4/${fl}_${pr}_s$sd/flight.ulg g4 $pr $fl $sd
done; done; done
# 4. G5.5
for sd in 1 2 3; do
  for sc in offb_vel_step o1_lemniscate o2_circle_z o3_lemniscate_gust o4_lemniscate_payload o5_zsine_com_shift o6_zsine_mass o7_lemniscate_tau2; do
    item g55_${sc}_s$sd $R/g55/${sc}_s$sd/flight.ulg fly g55 $sc $sd
  done
done
# 5. G5.3/G5.4 (+ hold row, as hold3.sh of g5_freeze_s157)
for sd in 1 2 3; do for sc in auto_tour auto_land10; do
  item g5_${sc}_s$sd $R/g5/${sc}_s$sd/flight.ulg fly g5 $sc $sd
done; item g5_hold_wind_s$sd $R/g5/hold_wind_s$sd/flight.ulg fly g5 hold_wind $sd --stick-mode posctl --scenario-overrides $HW; done
# 6. G5 event rows in hover, 1 seed (batch2.sh runev of g5_freeze_s157)
item events_s1 $R/events/g5_events_s1/flight.ulg ev 1
# 7. G2-STEP attitude cell, 3 seeds
for sd in 1 2 3; do for sc in step_roll step_pitch step_yaw; do
  item step_${sc}_s$sd $R/steps/seed$sd/${sc}_indi/flight.ulg step $sd $sc
done; done
echo "$(stamp) QUEUE_END" >> $R/queue.log
