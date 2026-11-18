#!/bin/bash
# S116 nominal lemniscate baseline (c1, c2). Serial: one container at a time. Progress appended to progress_c.txt.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi || exit 1
D=indi_flight/results/g3_ladder_s116
P=$D/progress_c.txt
BP=indi_flight/bench/params/quad5in_indi_g1.params
COMMON="--model quad5in --sim v2 --rate-hz 800 --seed 768592122 --sim-seed 680969658"
run_row() {
  local NAME=$1; shift
  indi_project/docker/run.sh -n g3c_$NAME -t 900 -- python3 indi_flight/bench/run_scenario.py $COMMON --out $D/$NAME "$@" > $D/$NAME.stdout 2>&1
  echo "$NAME rc=$?" >> $P
}
run_row lem_nominal_indi --scenario o1_lemniscate --controller indi --sched --params $BP
run_row lem_nominal_pid --scenario o1_lemniscate --controller pid_default --sched --params $BP
echo DONE >> $P
