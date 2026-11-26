#!/usr/bin/env bash
# Score the 4 flights, both keys, host python /tmp/g3venv; same flags as g3_score.sh (key 1 prints them) / g3_chain.sh (key 2).
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi || exit 1
. /tmp/g3venv/bin/activate
S=indi_flight/results/g3_cand_i_s231
B=indi_flight/bench
for n in joint:024 d264:024 d262:022 d283:283; do
  name=${n%%:*}; idx=${n##*:}; r=run_$idx
  bash $B/g3_score.sh $S/$name > $S/raw_key1_$name.txt 2>&1
  cp $S/$name/$r/g3_checks.json $S/raw_key1_$name.json
  args=$(grep -E "^$r (--t0|--run-json) " $S/raw_key1_$name.txt | head -1 | cut -d' ' -f2-)
  echo "$name $args" >> $S/score_args.txt
  python3 $B/g3_checks_key2.py $S/$name/$r $args --out $S/key2_$name > $S/raw_key2_$name.txt 2>&1
done
