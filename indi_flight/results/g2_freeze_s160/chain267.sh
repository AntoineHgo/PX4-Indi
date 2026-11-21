#!/bin/bash
# S165: G2 267 Hz "reported" cells (GATES G2: 1 rate + 1 outer cell), serial, reuses the freeze recipes.
cd "$(dirname "$0")/../../.." || exit 1
O=indi_flight/results/g2_outer_freeze_s163; R=indi_flight/results/g2_freeze_s160
timeout 1500 bash $O/fly.sh 1 3 267 1; echo "outer pt1 rc=$?" >> $R/chain267_status.txt
timeout 1500 bash $O/fly.sh 0 3 267 1; echo "outer pt0 rc=$?" >> $R/chain267_status.txt
CELLS="roll:267:1" timeout 1800 bash $R/batch.sh; echo "rate roll267 rc=$?" >> $R/chain267_status.txt
echo CHAIN267_END >> $R/chain267_status.txt
