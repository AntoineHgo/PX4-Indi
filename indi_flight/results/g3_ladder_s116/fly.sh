#!/bin/bash
# G3 single-factor ladder (S116). Serial: one container at a time.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi || exit 1
D=indi_flight/results/g3_ladder_s116
P=$D/progress.txt
: > $P
BASE="--scenario stick_zsine_o6 --controller indi --model quad5in --sim v2 --rate-hz 800 --seed 768592122 --sim-seed 680969658 --stick-mode stabilized --params indi_flight/bench/params/quad5in_indi_g1.params"
run_row() {
  local NAME=$1; shift
  indi_project/docker/run.sh -n g3l_$NAME -t 900 -- python3 indi_flight/bench/run_scenario.py $BASE --out $D/$NAME "$@" > $D/$NAME.stdout 2>&1
  echo "$NAME rc=$?" >> $P
}
run_row nominal
run_row mass13 --model-variant mass=1.3
run_row inert13 --model-variant ixx=1.3,iyy=1.3,izz=1.3
run_row sag07 --scenario-overrides $D/sag07.json
run_row wind5 --scenario-overrides $D/wind5.json
run_row erpmloss --scenario-overrides $D/erpmloss.json
run_row weak08 --scenario-overrides $D/weak08.json
run_row sat --scenario-overrides $D/sat.json
run_row gnssmis --gps-dly 150 --gnss-delay 0
echo DONE >> $P
