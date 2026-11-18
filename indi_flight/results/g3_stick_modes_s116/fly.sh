#!/bin/bash
# G3 stick-mode pre-test (S116): nominal ladder row with altctl/posctl stick modes. Serial.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi || exit 1
D=indi_flight/results/g3_stick_modes_s116
P=$D/progress.txt
: > $P
BASE="--scenario stick_zsine_o6 --controller indi --model quad5in --sim v2 --rate-hz 800 --seed 768592122 --sim-seed 680969658 --params indi_flight/bench/params/quad5in_indi_g1.params"
run_row() {
  local NAME=$1; shift
  indi_project/docker/run.sh -n g3sm_$NAME -t 900 -- python3 indi_flight/bench/run_scenario.py $BASE --out $D/$NAME "$@" > $D/$NAME.stdout 2>&1
  echo "$NAME rc=$?" >> $P
}
run_row m1_altctl --stick-mode altctl
run_row m2_posctl --stick-mode posctl
run_row m3_posctl_sag07 --stick-mode posctl --scenario-overrides indi_flight/results/g3_ladder_s116/sag07.json
echo DONE >> $P
