#!/bin/sh
# run in docker from repo root: score.sh
P=indi_flight/results/chatter_probe_s178; R=indi_flight/results/g4_fix_probe_s179; S=$R/score
sh indi_flight/bench/gate_g4.sh score $S
sed "s#chatter_probe_s178/score#g4_fix_probe_s179/score#" $P/rescore_key1.py | python3 -
sed -e "s#chatter_probe_s178/score#g4_fix_probe_s179/score#" -e "s#(\"cruise_p1_s1\", \"cruise_p2_s1\")#(\"cruise_f1_s1\", \"cruise_f1_s2\", \"cruise_f1_s3\")#" $P/score_key2.py | python3 -
python3 indi_flight/results/g4_gate_s169/chatter_cruise_s176.py $S/cruise_f1_s?
