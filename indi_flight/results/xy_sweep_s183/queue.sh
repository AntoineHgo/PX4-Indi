#!/usr/bin/env bash
# S183 xy gain sweep: pairs (XY_P 1.2, XY_VP 2.4|2.8); per pair 2 G2 spot cells + 3 G5.5 flights. Serial, idempotent.
cd "$(dirname "$0")/../../.." || exit 1
R=indi_flight/results/xy_sweep_s183; F8=indi_flight/results/freeze8_s181; P0=indi_flight/results/g5_freeze_s157/params.params
S=$R/queue_status.tsv; [ -f $S ] || printf 'name\tstart\tend\trc\n' > $S
stamp() { date '+%F %T'; }
item() { local n=$1 o=$2; shift 2; [ -s $o ] && return
  docker ps -q --filter name=s183sw | xargs -r docker stop >/dev/null
  local t0; t0=$(stamp); "$@"; local rc=$?; printf '%s\t%s\t%s\t%s\n' "$n" "$t0" "$(stamp)" $rc >> $S; }
PLANT="--model quad5in --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0"
fly() { # fly <vp> <scenario> <seed>   (freeze8 queue.sh fly() with XY params appended to params file)
  local vp=$1 sc=$2 sd=$3 d=$R/vp$1/g55; mkdir -p $d; local o=$d/${2}_s$3
  cp $P0 $o.params; printf 'MC_INDI_XY_P 1.2\nMC_INDI_XY_VP %s\n' $vp >> $o.params
  timeout 1000 indi_project/docker/run.sh -n s183sw${vp}${sc}_s$sd -t 900 -- python3 indi_flight/bench/run_scenario.py --controller indi \
    $PLANT --seed $sd --params $o.params --scenario $sc --out $o > $o.stdout.log 2>&1
  python3 indi_flight/bench/g55_check.py $o --json $o/g55.json > $o.check.txt 2>&1; }
for vp in 2.4 2.8; do
  item rate_$vp $R/vp$vp/roll800_fwdef_s2/margins.txt bash $R/fly.sh rate $vp
  item att_$vp $R/vp$vp/ax2_r400_s1_margins.json bash $R/fly.sh att $vp
  for sc in o1_lemniscate o3_lemniscate_gust o7_lemniscate_tau2; do
    item g55_${sc}_$vp $R/vp$vp/g55/${sc}_s1/flight.ulg fly $vp $sc 1
  done
done
echo "$(stamp) QUEUE_END" >> $R/queue.log
