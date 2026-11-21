#!/usr/bin/env bash
# S163 tail: after the outer batch, re-fly yaw400_s1 (sim-hole invalid), then hole reports + key2 for every rate cell. Serial.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi || exit 1
G=indi_flight/results/g2_freeze_s160
until grep -q "OUTER_END\|ABORT" indi_flight/results/g2_outer_freeze_s163/batch.log 2>/dev/null; do sleep 30; done
CELLS="yaw:400:1" bash $G/batch.sh >> $G/batch_s163.log 2>&1
indi_project/docker/run.sh -n s163holes -t 1200 -- bash -c "for d in $G/*_s[0-9]; do python3 indi_flight/bench/hole_report.py \$d/s1/flight.ulg > \$d/holes.txt 2>&1; done"
indi_project/docker/run.sh -n s163key -t 1200 -- bash $G/key2_all.sh > $G/key2_all.log 2>&1
echo FINAL_END
