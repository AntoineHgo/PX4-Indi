#!/bin/bash
# S116 control flights (b1..b6). Serial: one container at a time. Progress appended to progress_b.txt.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi || exit 1
D=indi_flight/results/g3_ladder_s116
P=$D/progress_b.txt
BP=indi_flight/bench/params/quad5in_indi_g1.params
COMMON="--model quad5in --sim v2 --rate-hz 800 --seed 768592122 --sim-seed 680969658"
run_row() {
  local NAME=$1; shift
  indi_project/docker/run.sh -n g3b_$NAME -t 900 -- python3 indi_flight/bench/run_scenario.py $COMMON --out $D/$NAME "$@" > $D/$NAME.stdout 2>&1
  echo "$NAME rc=$?" >> $P
}
run_row pid_sag07 --scenario stick_zsine_o6 --controller pid_default --stick-mode stabilized --params $BP --scenario-overrides $D/sag07.json
run_row pid_weak08 --scenario stick_zsine_o6 --controller pid_default --stick-mode stabilized --params $BP --scenario-overrides $D/weak08.json
run_row lem_sag07 --scenario o1_lemniscate --controller indi --sched --params $BP --scenario-overrides $D/sag07.json
run_row lem_weak08 --scenario o1_lemniscate --controller indi --sched --params $BP --scenario-overrides $D/weak08_lem.json
run_row lem_sat --scenario o1_lemniscate --controller indi --sched --params $BP --scenario-overrides $D/sat_lem.json
run_row lem_wind5 --scenario o1_lemniscate --controller indi --sched --params $BP --scenario-overrides $D/wind5_lem.json
echo DONE >> $P
