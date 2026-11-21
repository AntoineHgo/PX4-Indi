#!/bin/bash
# Run in Docker: indi_project/docker/run.sh -n a56pidana -t 900 -- bash indi_flight/results/a56_pid_s173/analyse.sh
# Item 2 is whole-flight (D-G3-SPAN); --t0/--t1 (37/92 s, as the INDI harsh runs) only set the item-3 window.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
O=indi_flight/results/a56_pid_s173
for r in $O/pid_hover_harsh_s2 $O/pid_hover_harsh_s3; do
  python3 indi_flight/bench/g3_checks.py $r/flight.ulg --t0 37 --t1 92 > $r/g3_checks.json 2>$r/g3_checks.err
  echo "G3 $(basename $r) rc $?"
done
