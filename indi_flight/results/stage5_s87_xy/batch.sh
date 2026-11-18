#!/usr/bin/env bash
# S87 xy batch: every remaining cell, serially (S86 finding 1). Skips cells whose margins json exists.
cd "$(dirname "$0")/../../.."
for S in 1 2; do for R in 400 800; do for PT in 0 1; do for AX in 1 2; do
  N=pt${PT}_ax${AX}_r${R}_s${S}
  [ -s indi_flight/results/stage5_s87_xy/${N}_margins.json ] && continue
  bash indi_flight/results/stage5_s87_xy/fly.sh $PT $AX $R $S
done; done; done; done
echo BATCH_END
