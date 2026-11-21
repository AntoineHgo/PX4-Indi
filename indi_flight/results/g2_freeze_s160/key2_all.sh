#!/usr/bin/env bash
# Second key (bench/second_key_m3a_s100.py, independent of m3a_margins_pretest.py, K100/K101) over every rate cell with margins.txt.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi || exit 1
G=indi_flight/results/g2_freeze_s160
declare -A A=([roll]=0 [pitch]=1 [yaw]=2)
for d in $G/*_s[0-9]; do n=$(basename $d); ax=${n%%[0-9]*}
  [ -s $d/margins.txt ] || continue; [ -s $d/key2.md ] && continue
  python3 indi_flight/bench/second_key_m3a_s100.py --axis ${A[$ax]} $d/s1/flight.ulg $d/key2.md $d/margins.txt > $d/key2_stdout.txt 2>&1
  echo "$n rc=$?"
done
