#!/usr/bin/env bash
# K101: second key of the 12 model-only rate cells (S100 P100 + B100), bench/second_key_m3a_s100.py --axis N.
G=indi_flight/results/g2_rate_modelonly_s100
for d in P400:1 Y800:2 roll800_s1:0 roll800_s2:0 roll400_s1:0 roll400_s2:0 pitch800_s1:1 pitch800_s2:1 pitch400_s2:1 yaw400_s1:2 yaw400_s2:2 yaw800_s2:2; do
  c=${d%%:*}; a=${d##*:}
  python3 indi_flight/bench/second_key_m3a_s100.py --axis $a $G/$c/s1/flight.ulg $G/key_k101/$c.md $G/$c/margins.txt > $G/key_k101/$c.stdout 2>&1 || echo "$c FAIL" 
  echo "$c done"
done
