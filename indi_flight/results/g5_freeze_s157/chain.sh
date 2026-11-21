#!/usr/bin/env bash
# S157 detached chain: wait for batch.sh (bg job) to end, resume it, then batch2.sh. Repo root.
cd "$(dirname "$0")/../../.."
D=indi_flight/results/g5_freeze_s157
while pgrep -f "g5_freeze_s157/batch.sh" >/dev/null; do sleep 30; done
bash $D/batch.sh; bash $D/batch2.sh
echo CHAIN_END >> $D/batch_status.txt
