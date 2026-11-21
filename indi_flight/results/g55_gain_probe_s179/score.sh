#!/bin/sh
# run in docker from repo root. Same as g4_fix_probe_s179/score.sh, run dir cruise_typ_s1 (symlink in score/)
P=indi_flight/results/chatter_probe_s178; R=indi_flight/results/g55_gain_probe_s179; S=$R/score
sh indi_flight/bench/gate_g4.sh score $S
sed "s#chatter_probe_s178/score#g55_gain_probe_s179/score#" $P/rescore_key1.py | python3 -
sed -e "s#chatter_probe_s178/score#g55_gain_probe_s179/score#" -e "s#(\"cruise_p1_s1\", \"cruise_p2_s1\")#(\"cruise_typ_s1\",)#" $P/score_key2.py | python3 -
python3 indi_flight/results/g4_gate_s169/chatter_cruise_s176.py $S/cruise_typ_s1
