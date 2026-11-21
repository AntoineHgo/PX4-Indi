#!/bin/sh
# docker, repo root. Copy of f4_probe_s180/score.sh with paths changed, runs cruise_typ_s2 and s3. RAW into this folder.
R=indi_flight/results/freeze8_pretest_s181; S=$R/score; P=indi_flight/results/chatter_probe_s178
mkdir -p $S; for n in cruise_typ_s2 cruise_typ_s3; do ln -sfn ../$n $S/$n; done
sh indi_flight/bench/gate_g4.sh score $S
sed "s#chatter_probe_s178/score#freeze8_pretest_s181/score#" $P/rescore_key1.py | python3 -
sed -e "s#chatter_probe_s178/score#freeze8_pretest_s181/score#" -e "s#(\"cruise_p1_s1\", \"cruise_p2_s1\")#(\"cruise_typ_s2\", \"cruise_typ_s3\")#" $P/score_key2.py | python3 -
for n in cruise_typ_s2 cruise_typ_s3; do
RAW=$R/chatter_raw_$n.txt python3 indi_flight/results/g4_gate_s169/chatter_cruise_s176.py $S/$n
done
python3 indi_flight/bench/g4_chatter_skip_key1.py $R/skip_key1.md $S/cruise_typ_s2 $S/cruise_typ_s3
python3 indi_flight/bench/g4_chatter_skip_key2.py $S/cruise_typ_s2 $S/cruise_typ_s3
