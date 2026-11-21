#!/bin/sh
# docker, repo root
R=indi_flight/results/f4_probe_s180; S=$R/score; P=indi_flight/results/chatter_probe_s178; G=indi_flight/results/g55_gain_probe_s179
sh indi_flight/bench/gate_g4.sh score $S
sed "s#chatter_probe_s178/score#f4_probe_s180/score#" $P/rescore_key1.py | python3 -
sed -e "s#chatter_probe_s178/score#f4_probe_s180/score#" -e "s#(\"cruise_p1_s1\", \"cruise_p2_s1\")#(\"cruise_typ_s1\",)#" $P/score_key2.py | python3 -
RAW=$R/chatter_raw.txt python3 indi_flight/results/g4_gate_s169/chatter_cruise_s176.py $S/cruise_typ_s1
python3 indi_flight/bench/g4_chatter_skip_key1.py $R/skip_key1.md $S/cruise_typ_s1
python3 indi_flight/bench/g4_chatter_skip_key2.py $S/cruise_typ_s1
