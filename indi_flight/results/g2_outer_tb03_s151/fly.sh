#!/usr/bin/env bash
# S151 G2 outer accel-break cell at MC_INDI_POS_TB 0.3 + kMaxBlend 0.5 (D-GAP-G510 accept condition).
# Usage: fly.sh PT AX RATE SEED (from repo root). Base params: results/g5_g510_s150/params_tb03.params;
# injection settings as S86 (results/stage5_s86_g2outer/fly.sh): AMP 0.04, TP 10, NP 5, DLY 20, band 0.2-8 Hz.
set -u
PT=$1; AX=$2; RATE=$3; SEED=$4
D=indi_flight/results/g2_outer_tb03_s151
N=pt${PT}_ax${AX}_r${RATE}_s${SEED}
grep -v '^#' indi_flight/results/g5_g510_s150/params_tb03.params | grep -v -e '^MC_INDI_PINJ_' > $D/$N.params
printf 'MC_INDI_PINJ_AX %s\nMC_INDI_PINJ_PT %s\nMC_INDI_PINJ_AMP 0.04\nMC_INDI_PINJ_TP 10\nMC_INDI_PINJ_FLO 0.2\nMC_INDI_PINJ_FHI 8\nMC_INDI_PINJ_NP 5\nMC_INDI_PINJ_DLY 20\n' "$AX" "$PT" >> $D/$N.params
POINT=input; [ "$PT" = 1 ] && POINT=output
indi_project/docker/run.sh -n s151$N -t 900 -- python3 indi_flight/bench/run_scenario.py --scenario hover_long \
  --controller indi --model quad5in --sim v2 --rate-hz $RATE --seed $SEED --speed 4 --gps-dly 110 --gnss-delay 110 \
  --params $D/$N.params --out $D/$N > $D/$N.stdout.log 2>&1
indi_project/docker/run.sh -n s151a$N -t 240 -- python3 indi_flight/bench/pinj_csv.py $D/$N/flight.ulg $((AX-1)) \
  $D/${N}_pinj.csv --Tp 10 --fmin 0.2 --fmax 8 --margins --point $POINT > $D/${N}_margins.json 2> $D/${N}_margins.err
indi_project/docker/run.sh -n s151h$N -t 240 -- python3 indi_flight/bench/hole_report.py $D/$N/flight.ulg \
  > $D/${N}_holes.txt 2>&1
echo "$N done"
