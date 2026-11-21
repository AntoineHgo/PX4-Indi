#!/usr/bin/env bash
# S163 G2 outer cells at the stage-6 freeze (D-FREEZE-6 plant: freeze params, matched GNSS 110, G4 typical noise).
# Recipe = results/g2_outer_tb03_s151/fly.sh with base results/g5_freeze_s157/params.params and the typical-noise flags.
# Usage (repo root): fly.sh PT AX RATE SEED ; xy: AMP=0.08 TP=20 SCN=hover_xlong. Skips a cell whose margins json is non-empty.
set -u
PT=$1; AX=$2; RATE=$3; SEED=$4
D=indi_flight/results/g55_gain_probe_s179
N=pt${PT}_ax${AX}_r${RATE}_s${SEED}
[ -s $D/${N}_margins.json ] && { echo "$N skip"; exit 0; }
{ grep -v '^#' indi_flight/results/g55_gain_probe_s179/params_xyp12.params | grep -v -e '^MC_INDI_PINJ_'; } > $D/$N.params
printf "MC_INDI_PINJ_AX %s\nMC_INDI_PINJ_PT %s\nMC_INDI_PINJ_AMP ${AMP:-0.04}\nMC_INDI_PINJ_TP ${TP:-10}\nMC_INDI_PINJ_FLO 0.2\nMC_INDI_PINJ_FHI 8\nMC_INDI_PINJ_NP 5\nMC_INDI_PINJ_DLY 20\n" "$AX" "$PT" >> $D/$N.params
POINT=input; [ "$PT" = 1 ] && POINT=output
if [ ! -f $D/$N/flight.ulg ]; then timeout 1300 indi_project/docker/run.sh -n s179gp$N -t 1200 -- python3 indi_flight/bench/run_scenario.py --scenario ${SCN:-hover_long} \
  --controller indi --model quad5in --sim v2 --rate-hz $RATE --seed $SEED --speed 4 --gps-dly 110 --gnss-delay 110 \
  --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0 --params $D/$N.params --out $D/$N > $D/$N.stdout.log 2>&1; fi
timeout 300 indi_project/docker/run.sh -n s179gpa$N -t 240 -- python3 indi_flight/bench/pinj_csv.py $D/$N/flight.ulg $((AX-1)) \
  $D/${N}_pinj.csv --Tp ${TP:-10} --fmin 0.2 --fmax 8 --margins --point $POINT > $D/${N}_margins.json 2> $D/${N}_margins.err
timeout 300 indi_project/docker/run.sh -n s179gph$N -t 240 -- python3 indi_flight/bench/hole_report.py $D/$N/flight.ulg \
  > $D/${N}_holes.txt 2>&1
echo "$N done"
