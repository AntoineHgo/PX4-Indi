#!/usr/bin/env bash
# S107 attitude-loop break pre-test (MC_INDI_INJ_PT 1, rate-setpoint break), serial, hover_xlong.
# Usage: fly.sh AX RATE SEED RAMP   (AX 1|2|3 = roll|pitch|yaw; RAMP rad/s per sine component). Run from repo root.
set -u
AX=$1; RATE=$2; SEED=$3; RAMP=$4
D=indi_flight/results/g2_attbreak_s107
N=ax${AX}_r${RATE}_s${SEED}_a${RAMP}
grep -v '^#' indi_flight/results/stage5_s84_accbreak/pt1.params | grep -v PINJ > $D/$N.params
printf 'MC_INDI_INJ_AX %s\nMC_INDI_INJ_PT 1\nMC_INDI_INJ_RAMP %s\nMC_INDI_INJ_TP 10\nMC_INDI_INJ_FMIN 0.2\nMC_INDI_INJ_FMAX 20\nMC_INDI_INJ_NP 5\nMC_INDI_INJ_DLY 20\n' "$AX" "$RAMP" >> $D/$N.params
indi_project/docker/run.sh -n s107$N -t 1500 -- python3 indi_flight/bench/run_scenario.py --scenario hover_xlong \
  --controller indi --model quad5in --sim v2 --rate-hz $RATE --seed $SEED --speed 4 \
  --params $D/$N.params --out $D/$N > $D/$N.stdout.log 2>&1
indi_project/docker/run.sh -n s107c$N -t 240 -- python3 indi_flight/bench/attitude_break_check.py $D/$N/flight.ulg $((AX-1)) \
  --Tp 10 --fmin 0.2 --fmax 20 > $D/${N}_check.txt 2>&1
indi_project/docker/run.sh -n s107h$N -t 240 -- python3 indi_flight/bench/hole_report.py $D/$N/flight.ulg > $D/${N}_holes.txt 2>&1
echo "$N done"
