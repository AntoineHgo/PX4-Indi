#!/usr/bin/env bash
# Freeze-7 re-fly queue (D-FREEZE-7), serial and idempotent. Resume = rerun this script from anywhere.
# Order: G5.5 (8 scenarios x 3 seeds = 24), G4 (18, bench/gate_g4.sh), G5.3/G5.4 (auto_tour, auto_land10 x 3 = 6).
# An item is skipped when its out dir has flight.ulg. Runner args copied from g5_freeze_s157/fly.sh (freeze config).
cd "$(dirname "$0")/../../.." || exit 1
R=indi_flight/results/freeze7_s177; P=indi_flight/results/g5_freeze_s157/params.params
S=$R/queue_status.tsv; mkdir -p $R/g55 $R/g4 $R/g5
[ -f $S ] || printf 'name\tstart\tend\trc\n' > $S
stamp() { date '+%F %T'; }
item() { # item <name> <outdir> <cmd...>
  local n=$1 o=$2; shift 2
  [ -f $o/flight.ulg ] && return
  docker ps -q --filter name=s177 | xargs -r docker stop >/dev/null
  local t0; t0=$(stamp); "$@"; local rc=$?
  printf '%s\t%s\t%s\t%s\n' "$n" "$t0" "$(stamp)" $rc >> $S
}
fly() { # fly <group> <scenario> <seed>
  local g=$1 sc=$2 sd=$3 o=$R/$1/${2}_s$3
  timeout 1000 indi_project/docker/run.sh -n s177${sc}_s$sd -t 900 -- python3 indi_flight/bench/run_scenario.py --controller indi \
    --model quad5in --seed $sd --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 \
    --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0 \
    --params $P --scenario $sc --out $o > $o.stdout.log 2>&1
}
g4() { timeout 1000 sh indi_flight/bench/gate_g4.sh fly $R/g4 "$1" "$2" "$3"; }
for sd in 1 2 3; do
  for sc in offb_vel_step o1_lemniscate o2_circle_z o3_lemniscate_gust o4_lemniscate_payload o5_zsine_com_shift o6_zsine_mass o7_lemniscate_tau2; do
    item g55_${sc}_s$sd $R/g55/${sc}_s$sd fly g55 $sc $sd
  done
done
for sd in 1 2 3; do for pr in quiet typ harsh; do for fl in hover cruise; do
  item g4_${fl}_${pr}_s$sd $R/g4/${fl}_${pr}_s$sd g4 $pr $fl $sd
done; done; done
for sd in 1 2 3; do for sc in auto_tour auto_land10; do
  item g5_${sc}_s$sd $R/g5/${sc}_s$sd fly g5 $sc $sd
done; done
echo "$(stamp) QUEUE_END" >> $R/queue.log
