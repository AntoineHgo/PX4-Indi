#!/usr/bin/env bash
# S86 G2 outer-loop cells (preliminary, pre-freeze): one flight + analysis per cell.
# Usage: fly.sh PT AX RATE SEED   (PT 0 = stage input / velocity-position break, 1 = stage output / accel break;
#        AX 1|2|3 = x|y|z NED; RATE 400|800). Run from the repository root.
set -u
PT=$1; AX=$2; RATE=$3; SEED=$4
D=indi_flight/results/stage5_s86_g2outer
N=pt${PT}_ax${AX}_r${RATE}_s${SEED}
grep -v '^#' indi_flight/results/stage5_s84_accbreak/pt1.params | grep -v -e '^MC_INDI_PINJ_AX' -e '^MC_INDI_PINJ_PT' > $D/$N.params
printf 'MC_INDI_PINJ_AX %s\nMC_INDI_PINJ_PT %s\n' "$AX" "$PT" >> $D/$N.params
POINT=input; [ "$PT" = 1 ] && POINT=output
indi_project/docker/run.sh -n s86$N -t 900 -- python3 indi_flight/bench/run_scenario.py --scenario hover_long \
  --controller indi --model quad5in --sim v2 --rate-hz $RATE --seed $SEED --speed 4 \
  --params $D/$N.params --out $D/$N > $D/$N.stdout.log 2>&1
indi_project/docker/run.sh -n s86a$N -t 240 -- python3 indi_flight/bench/pinj_csv.py $D/$N/flight.ulg $((AX-1)) \
  $D/${N}_pinj.csv --Tp 10 --fmin 0.2 --fmax 8 --margins --point $POINT > $D/${N}_margins.json 2> $D/${N}_margins.err
indi_project/docker/run.sh -n s86h$N -t 240 -- python3 indi_flight/bench/hole_report.py $D/$N/flight.ulg \
  > $D/${N}_holes.txt 2>&1
echo "$N done"
