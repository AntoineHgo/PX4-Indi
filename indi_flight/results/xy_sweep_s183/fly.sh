#!/usr/bin/env bash
# S178 G2 spot-check cells at freeze-7 (Q16 answer A). Recipes copied from the freeze-6 cells:
#   rate: g2_freeze_s160/batch.sh (S138 injection, check_rates/pretest_gate/m3a_csv/m3a_margins_pretest)
#   att : g2_att_freeze_s162/batch.sh (rate-setpoint break, attitude_break_check/hole_report/ratesp_csv --margins)
# Usage (repo root): fly.sh rate|att ; cells are fixed below. Skips a cell whose margins output is non-empty.
set -u
cd "$(dirname "$0")/../../.." || exit 1
XP=1.2; VP=${2:?vp}; D=indi_flight/results/xy_sweep_s183/vp$VP; mkdir -p $D; G6=indi_flight/results/g2_freeze_s160; G62=indi_flight/results/g2_att_freeze_s162
NOISE="--gps-dly 110 --gnss-delay 110 --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0"
case $1 in
rate)  # roll 800 Hz firmware-default cell (ID_OK 0, W_MAX 0, ACT_TC 0.05), seed 2; INJ_AX 1 roll
  N=roll800_fwdef_s2; HZ=800; SEED=2; mkdir -p $D/$N
  [ -s $D/$N/margins.txt ] && { echo "$N skip"; exit 0; }
  cp $G6/params_fwdef_roll.params $D/$N.params; printf 'MC_INDI_XY_P %s\nMC_INDI_XY_VP %s\n' $XP $VP >> $D/$N.params
  [ -f $D/$N/s1/flight.ulg ] || timeout 1000 indi_project/docker/run.sh -n s183sw${VP}f$N -t 900 -- python3 indi_flight/bench/run_scenario.py \
    --scenario hover_long --controller indi --seed $SEED --speed 4 --model quad5in --rate-hz $HZ --sim v2 $NOISE \
    --params $D/$N.params --out $D/$N/s1 > $D/$N/stdout.log 2>&1
  timeout 700 indi_project/docker/run.sh -n s183sw${VP}p$N -t 600 -- bash -c "python3 indi_flight/bench/check_rates.py $D/$N/s1 > $D/$N/rates.txt 2>&1; \
    python3 indi_flight/bench/pretest_gate.py $D/$N/s1/flight.ulg $D/$N/gate.md --delay 4 --length 15 > $D/$N/gate_stdout.txt 2>&1; \
    python3 indi_flight/bench/m3a_csv.py $D/$N/s1/flight.ulg 0 $D/$N/s1.csv > $D/$N/csv_stdout.txt 2>&1; \
    python3 indi_flight/bench/m3a_margins_pretest.py $D/$N/s1.csv 1 60 10 $HZ > $D/$N/margins.txt 2>&1; \
    python3 indi_flight/bench/hole_report.py $D/$N/s1/flight.ulg > $D/$N/holes.txt 2>&1" > $D/$N/post.log 2>&1
  echo "$N done" ;;
att)   # pitch 400 Hz attitude cell (rate-setpoint break), seed 1; ax 2 = pitch
  AX=2; HZ=400; SEED=1; N=ax${AX}_r${HZ}_s${SEED}
  grep -q pm_deg $D/${N}_margins.json 2>/dev/null && { echo "$N skip"; exit 0; }
  cp $G62/params_base.params $D/$N.params
  printf 'MC_INDI_INJ_AX %s\nMC_INDI_INJ_PT 1\nMC_INDI_INJ_RAMP 0.06\nMC_INDI_INJ_TP 10\nMC_INDI_INJ_FMIN 0.2\nMC_INDI_INJ_FMAX 20\nMC_INDI_INJ_NP 5\nMC_INDI_INJ_DLY 20\n' $AX >> $D/$N.params; printf 'MC_INDI_XY_P %s\nMC_INDI_XY_VP %s\n' $XP $VP >> $D/$N.params
  [ -f $D/$N/flight.ulg ] || timeout 1600 indi_project/docker/run.sh -n s183sw${VP}f$N -t 1500 -- python3 indi_flight/bench/run_scenario.py --scenario hover_xlong \
    --controller indi --model quad5in --sim v2 --rate-hz $HZ --seed $SEED --speed 4 $NOISE --params $D/$N.params --out $D/$N > $D/$N.stdout.log 2>&1
  timeout 300 indi_project/docker/run.sh -n s183sw${VP}c$N -t 240 -- python3 indi_flight/bench/attitude_break_check.py $D/$N/flight.ulg $((AX-1)) --Tp 10 --fmin 0.2 --fmax 20 > $D/${N}_check.txt 2>&1
  timeout 300 indi_project/docker/run.sh -n s183sw${VP}h$N -t 240 -- python3 indi_flight/bench/hole_report.py $D/$N/flight.ulg > $D/${N}_holes.txt 2>&1
  timeout 300 indi_project/docker/run.sh -n s183sw${VP}m$N -t 240 -- python3 indi_flight/bench/ratesp_csv.py $D/$N/flight.ulg $((AX-1)) $D/${N}_att.csv --Tp 10 --fmin 0.2 --fmax 20 --margins > $D/${N}_margins.json 2> $D/${N}_margins.err
  echo "$N done" ;;
esac
