#!/usr/bin/env bash
# S160: G5.3 hold row re-fly at the freeze plant (missing from batch/batch2). Serial, repo root, 3 seeds.
D=indi_flight/results/g5_freeze_s157
for s in 1 2 3; do
  [ -f $D/hold_wind_s$s/run.json ] && continue
  bash $D/fly.sh hold_wind $s --stick-mode posctl --scenario-overrides $D/hold_wind_overrides.json
done
echo HOLD3_END
