#!/usr/bin/env bash
# S135 G5.4 first 3-seed batch (probe, pre-freeze RC113): auto_tour (take-off, mission, RTL) and auto_land10, seeds 1-3.
# Serial, from the repo root. Skips runs whose flight.ulg exists (resume = rerun this script).
cd "$(dirname "$0")/../../.."
D=indi_flight/results/g5_probe_s135
for sc in auto_tour auto_land10; do for s in 1 2 3; do
  out=$D/${sc}_s$s; [ -f $out/flight.ulg ] && continue
  docker ps -q --filter name=px4-indi-g5 | xargs -r docker stop >/dev/null
  timeout 600 indi_project/docker/run.sh -n g5${sc}$s -t 500 -- python3 indi_flight/bench/run_scenario.py --scenario $sc \
    --controller indi --model quad5in --seed $s --speed 4 --sim v2 --params $D/params.params --out $out > $D/${sc}_s$s.log 2>&1
  echo "$sc s$s rc=$?" >> $D/batch_status.txt
done; done
echo DONE >> $D/batch_status.txt
