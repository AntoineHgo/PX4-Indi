#!/bin/bash
# Run in Docker: indi_project/docker/run.sh -n a56ana -t 1200 -- bash indi_flight/results/a56_probe_s173/analyse.sh
# Same computation as results/g4_jffoffb_s172/analyse.sh (G4 window, g3_checks item 2, omega/descent q std).
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
O=indi_flight/results/a56_probe_s173
for cfg in pos0 lpf4; do
  sh indi_flight/bench/gate_g4.sh score $O/$cfg
  for r in $O/$cfg/hover_harsh_s?; do
    n=$(basename $r)
    read t0 t1 < <(awk -v n="$n" -F'|' 'index($0,"| "n" |")==1{gsub(/ /,"",$3); split($3,a,"-"); print a[1], a[2]}' $O/$cfg/g4_table.md)
    python3 indi_flight/bench/g3_checks.py $r/flight.ulg --t0 $t0 --t1 $t1 > $r/g3_checks.json 2>$r/g3_checks.err
    echo "G3 $cfg $n rc $? t0=$t0 t1=$t1"
    python3 -I indi_flight/results/g4_jffoffb_s172/omega_offb.py $r
  done
done
