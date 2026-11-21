#!/bin/bash
# g3_checks.py per hover run, window = G4 window (hold+5 s .. end, ulog base), as the s169 g3_checks.json files
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight || exit 1
for r in results/g4_jff_s172/hover_*_s?; do
  n=$(basename $r); read t0 t1 < <(awk -v n="$n" -F'|' 'index($0,"| "n" |")==1{gsub(/ /,"",$3); split($3,a,"-"); print a[1], a[2]}' results/g4_jff_s172/g4_table.md)
  python3 bench/g3_checks.py $r/flight.ulg --t0 $t0 --t1 $t1 > $r/g3_checks.json 2>$r/g3_checks.err
  echo "$n rc $? t0=$t0 t1=$t1"
done
