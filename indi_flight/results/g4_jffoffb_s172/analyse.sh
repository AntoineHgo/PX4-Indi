#!/bin/bash
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
sh indi_flight/bench/gate_g4.sh score indi_flight/results/g4_jffoffb_s172
for r in indi_flight/results/g4_jffoffb_s172/hover_harsh_s?; do
  n=$(basename $r)
  read t0 t1 < <(awk -v n="$n" -F'|' 'index($0,"| "n" |")==1{gsub(/ /,"",$3); split($3,a,"-"); print a[1], a[2]}' indi_flight/results/g4_jffoffb_s172/g4_table.md)
  python3 indi_flight/bench/g3_checks.py $r/flight.ulg --t0 $t0 --t1 $t1 > $r/g3_checks.json 2>$r/g3_checks.err
  echo "G3 $n rc $? t0=$t0 t1=$t1"
  python3 -I indi_flight/results/g4_jffoffb_s172/omega_offb.py $r
done
