#!/bin/bash
# like-for-like: current g3_checks.py on the old S169 harsh hover runs, same G4 window as the new runs
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight || exit 1
for n in hover_harsh_s1 hover_harsh_s2 hover_harsh_s3; do
  read t0 t1 < <(awk -v n="$n" -F'|' 'index($0,"| "n" |")==1{gsub(/ /,"",$3); split($3,a,"-"); print a[1], a[2]}' results/g4_gate_s169/g4_table.md)
  python3 bench/g3_checks.py results/g4_gate_s169/$n/flight.ulg --t0 $t0 --t1 $t1 > results/g4_jff_s172/old_g3_$n.json 2>/dev/null
  echo "old $n rc $? t0=$t0 t1=$t1"
done
