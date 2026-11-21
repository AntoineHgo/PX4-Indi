#!/usr/bin/env bash
# FREEZE-10 gate re-fly queue (D-FREEZE-10, S193), serial. Firmware 7fe6206fcc, params results/g5_freeze_s157/params.params (XY gains at firmware defaults).
# Steps: 1 G3 pretest (20 draws, 2 keys) | 2 G5 (g5, g5_modes G5.1/5.2/5.7, g510_stab, g55, events) | 3 G4 (18 rows + scoring + Q20 guard) | 4 G2 (g2o, g2s, steps).
# Usage (repo root or anywhere): bash queue.sh [first_step=1]   e.g. `bash queue.sh 3` resumes at G4. Items with a done-file are skipped, so rerunning is safe.
# Each step continues after a scoring failure; the queue stops if the first flight of a step leaves no log (set-up fault).
cd "$(dirname "$0")/../../.." || exit 1
R=indi_flight/results/freeze10_s193; P=indi_flight/results/g5_freeze_s157/params.params; B=indi_flight/bench
HW=indi_flight/results/g5_freeze_s157/hold_wind_overrides.json
S=$R/queue_status.tsv; FROM=${1:-1}
mkdir -p $R/g2o $R/g2s $R/g55 $R/g4 $R/g5 $R/events $R/steps $R/g3_pretest $R/g5_modes $R/g510_stab
[ -f $S ] || printf 'name\tstart\tend\trc\n' > $S
stamp() { date '+%F %T'; }
stopall() { docker ps -q | xargs -r docker stop >/dev/null 2>&1; }
item() { # item <name> <donefile> <cmd...>
  local n=$1 o=$2; shift 2
  [ -s $o ] && return
  stopall
  local t0; t0=$(stamp); "$@"; local rc=$?
  printf '%s\t%s\t%s\t%s\n' "$n" "$t0" "$(stamp)" $rc >> $S
}
need() { # need <logfile> <step>: abort queue when the first flight of a step left no log
  [ -s $1 ] || { printf 'ABORT\t%s\t%s\t2\n' "$2 first flight missing: $1" "$(stamp)" >> $S; echo "$(stamp) ABORT $2" >> $R/queue.log; exit 2; }; }
PLANT="--model quad5in --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0"
fly() { local g=$1 sc=$2 sd=$3 o=$R/$1/${2}_s$3; shift 3
  timeout 1000 indi_project/docker/run.sh -n s193f10${sc}_s$sd -t 900 -- python3 $B/run_scenario.py --controller indi \
    $PLANT --seed $sd --params $P --scenario $sc "$@" --out $o > $o.stdout.log 2>&1; }
ev() { local o=$R/events/g5_events_s$1
  timeout 1000 indi_project/docker/run.sh -n s193f10g5_events_s$1 -t 900 -- python3 $B/g5_events.py --controller indi \
    $PLANT --seed $1 --params $P --out $o > $o.stdout.log 2>&1; }
step() { local sd=$1 sc=$2
  timeout 900 indi_project/docker/run.sh -n s193f10_${sc}_s$sd -t 900 -- python3 $B/run_scenario.py --scenario $sc --controller indi \
    --model quad5in --sim v2 --rate-hz 800 --seed $sd --speed 4 --params indi_flight/results/g2_step_s64/indi.params \
    --out $R/steps/seed$sd/${sc}_indi > $R/steps/seed${sd}_$sc.stdout 2>&1; }
g4() { timeout 1000 sh $B/gate_g4.sh fly $R/g4 "$1" "$2" "$3"; }
g2o() { timeout 1500 bash $R/g2o_fly.sh "$@"; }
g2s() { timeout 2000 bash $R/g2s_fly.sh "$@"; }

if [ $FROM -le 1 ]; then # ---- 1. G3 pre-test, 20 draws, both keys (fly_all.sh flies then scores key 1 + key 2)
  echo "$(stamp) STEP1 g3 start" >> $R/queue.log
  item g3_pretest $R/g3_pretest/SCORING_DONE_MARK timeout 36000 bash $R/g3_pretest/fly_all.sh 0 19
  need $R/g3_pretest/run_000/g3_done.json step1
  grep -q SCORING_DONE $R/g3_pretest/progress.txt 2>/dev/null && touch $R/g3_pretest/SCORING_DONE_MARK
fi

if [ $FROM -le 2 ]; then # ---- 2. G5
  echo "$(stamp) STEP2 g5 start" >> $R/queue.log
  item g5_modes $R/g5_modes/SCORE_DONE_MARK bash -c "bash $R/g5_modes/fly_all.sh; grep -q SCORE_DONE $R/g5_modes/batch_status.txt && touch $R/g5_modes/SCORE_DONE_MARK"
  need $R/g5_modes/stick_steps_s1_acro/flight.ulg step2
  for sd in 1 2 3; do item g510_indi_s$sd $R/g510_stab/indi_stab_s$sd.score_key2.txt bash $R/g510_stab/fly.sh indi $sd > $R/g510_stab/fly_indi_s$sd.out 2>&1; done
  # G5.4 / G5.3 typ+harsh rows of the probe (fly_a.sh of freeze10_cand_s191), flown into g5_modes
  HARSH="--model quad5in --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 --vib-acc 27 --vib-gyr 0 --imu-noise-scale 4.0"
  runm() { local tag=$1 pl=$2 sc=$3 sd=$4; shift 4
    timeout 1000 indi_project/docker/run.sh -n s193f10m_$tag -t 900 -- python3 $B/run_scenario.py --controller indi $pl --seed $sd --params $P \
      --scenario $sc "$@" --out $R/g5_modes/$tag > $R/g5_modes/$tag.stdout.log 2>&1; }
  item m_auto_land10_typ_s1 $R/g5_modes/auto_land10_typ_s1/flight.ulg runm auto_land10_typ_s1 "$PLANT" auto_land10 1
  item m_auto_tour_typ_s1 $R/g5_modes/auto_tour_typ_s1/flight.ulg runm auto_tour_typ_s1 "$PLANT" auto_tour 1
  item m_auto_tour_harsh_s1 $R/g5_modes/auto_tour_harsh_s1/flight.ulg runm auto_tour_harsh_s1 "$HARSH" auto_tour 1
  for sd in 1 2 3; do for sc in auto_tour auto_land10; do item g5_${sc}_s$sd $R/g5/${sc}_s$sd/flight.ulg fly g5 $sc $sd; done
    item g5_hold_wind_s$sd $R/g5/hold_wind_s$sd/flight.ulg fly g5 hold_wind $sd --stick-mode posctl --scenario-overrides $HW; done
  for sd in 1 2 3; do for sc in offb_vel_step o1_lemniscate o2_circle_z o3_lemniscate_gust o4_lemniscate_payload o5_zsine_com_shift o6_zsine_mass o7_lemniscate_tau2; do
    item g55_${sc}_s$sd $R/g55/${sc}_s$sd/flight.ulg fly g55 $sc $sd; done; done
  item events_s1 $R/events/g5_events_s1/flight.ulg ev 1
  # scoring (host python3 + pyulog, commands of freeze9_s183/G5_SCORES.md, both keys where a key2 exists)
  cd $R
  Bh=../../bench
  for d in g55/*_s?; do [ -f $d/flight.ulg ] && python3 $Bh/g55_check.py $d --json $d/g55.json > $d.check.txt 2>&1; done
  python3 $Bh/g55_g57_key2.py g55 g55/*_s? > g55/key2_g55.txt 2>&1
  for n in 1 2 3; do
    python3 $Bh/g53_mission_check.py g5/auto_tour_s$n --json g5/auto_tour_s$n/g53.json > g5/auto_tour_s$n.g53.check.txt 2>&1
    for r in auto_tour_s$n auto_land10_s$n; do python3 $Bh/auto_smoke_check.py g5/$r --json g5/$r/check.json > g5/$r.check.txt 2>&1; done; done
  python3 $Bh/g53_hold_check.py g5/hold_wind_s{1,2,3} > g5/g53_hold_check.txt 2>&1
  python3 $Bh/g53_hold_key2.py g5/hold_wind_s{1,2,3} > g5/key2_g53_hold.txt 2>&1
  python3 $Bh/g54_key2.py g5/auto_land10_s{1,2,3} > g5/key2_g54.txt 2>&1
  python3 $Bh/g54_land_key2.py g5/auto_land10_s{1,2,3} > g5/key2_g54_land.txt 2>&1
  python3 $Bh/g5_rows_check.py events/g5_events_s1 > events/g5_rows.txt 2>&1
  python3 $Bh/g511_check.py events/g5_events_s1 > events/g511.txt 2>&1
  python3 $Bh/g5_rows_key2.py events/g5_events_s1 > events/key2_g5rows_s1.txt 2>&1
  for r in auto_land10_typ_s1 auto_tour_typ_s1 auto_tour_harsh_s1; do [ -d g5_modes/$r ] && python3 $Bh/auto_smoke_check.py g5_modes/$r --json g5_modes/$r/check.json > g5_modes/$r.check.txt 2>&1; done
  for r in auto_tour_typ_s1 auto_tour_harsh_s1; do [ -d g5_modes/$r ] && python3 $Bh/g53_mission_check.py g5_modes/$r --json g5_modes/$r/g53.json > g5_modes/$r.g53.check.txt 2>&1; done
  python3 $Bh/g54_key2.py g5_modes/auto_land10_typ_s1 > g5_modes/key2_g54.txt 2>&1
  python3 $Bh/g54_land_key2.py g5_modes/auto_land10_typ_s1 > g5_modes/key2_g54_land.txt 2>&1
  cd - >/dev/null
  echo "$(stamp) STEP2 scoring done" >> $R/queue.log
fi

if [ $FROM -le 3 ]; then # ---- 3. G4: 18 flights, then scoring in docker (scipy)
  echo "$(stamp) STEP3 g4 start" >> $R/queue.log
  first=1
  for sd in 1 2 3; do for pr in quiet typ harsh; do for fl in hover cruise; do
    item g4_${fl}_${pr}_s$sd $R/g4/${fl}_${pr}_s$sd/flight.ulg g4 $pr $fl $sd
    [ $first = 1 ] && { need $R/g4/${fl}_${pr}_s$sd/flight.ulg step3; first=0; }
  done; done; done
  item g4_score $R/g4/g4_score.done timeout 3000 indi_project/docker/run.sh -n s193f10g4score -t 2900 -- bash $R/g4_score.sh
fi

if [ $FROM -le 4 ]; then # ---- 4. G2 outer cells (g2o_fly.sh also runs margins + hole report), spot cells, G2-STEP
  echo "$(stamp) STEP4 g2 start" >> $R/queue.log
  firstc=1
  for c in "1 3 800 1" "0 3 800 1" "1 3 400 1" "0 3 400 1" "1 3 800 2" "0 3 800 2" "1 3 400 2" "0 3 400 2"; do
    set -- $c; item g2o_pt$1_ax$2_r$3_s$4 $R/g2o/pt$1_ax$2_r$3_s$4_margins.json g2o $c
    [ $firstc = 1 ] && { need $R/g2o/pt$1_ax$2_r$3_s$4/flight.ulg step4; firstc=0; }
  done
  for s in 1 2; do for r in 800 400; do for ax in 1 2; do for pt in 1 0; do
    item g2o_pt${pt}_ax${ax}_r${r}_s$s $R/g2o/pt${pt}_ax${ax}_r${r}_s${s}_margins.json env AMP=0.08 TP=20 SCN=hover_xlong bash -c "timeout 1500 bash $R/g2o_fly.sh $pt $ax $r $s"
  done; done; done; done
  item g2s_rate $R/g2s/roll800_fwdef_s2/margins.txt g2s rate
  item g2s_att $R/g2s/ax2_r400_s1_margins.json g2s att
  for sd in 1 2 3; do for sc in step_roll step_pitch step_yaw; do
    item step_${sc}_s$sd $R/steps/seed$sd/${sc}_indi/flight.ulg step $sd $sc; done; done
fi
echo "$(stamp) QUEUE_END" >> $R/queue.log
