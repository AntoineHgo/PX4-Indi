#!/usr/bin/env bash
# brk.sh ID FILE OLD NEW TARGET : apply one text break, build+run TARGET in docker, revert, rebuild+run TARGET
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
G=indi_flight/results/g7_s251
ID=$1; F=$2; OLD=$3; NEW=$4; T=$5
cp "$F" /tmp/brk_backup_$$
python3 - "$F" "$OLD" "$NEW" <<'PY' || { echo "BREAK NOT APPLIED"; exit 1; }
import sys
f,o,n=sys.argv[1:4]
s=open(f).read()
assert s.count(o)==1, "pattern count %d"%s.count(o)
open(f,'w').write(s.replace(o,n))
PY
run() { indi_project/docker/run.sh -n s251_brk -t 1500 -- bash -c "B=build/px4_sitl_o11; ninja -C \$B $T 2>&1 | grep -E 'error' | head; \$B/$T 2>&1 | grep -E '^\[  (PASSED|FAILED)|Failure' | head -20" 2>&1 | tail -n 25; }
{ echo "== $ID: $F : '$OLD' -> '$NEW' ($T)"; echo "-- broken"; run; cp /tmp/brk_backup_$$ "$F"; echo "-- reverted"; run; } 2>&1 | tee $G/brk_$ID.txt
cp /tmp/brk_backup_$$ "$F"; rm /tmp/brk_backup_$$
