#!/usr/bin/env bash
# S135 G5.1 acro probe + A-46 closing test: stick_zsine_o6 --stick-mode acro, seeds 1-3 (S133 command).
# Serial, from the repo root. Skips runs whose flight.ulg exists (resume = rerun this script).
cd "$(dirname "$0")/../../.."
D=indi_flight/results/g5_probe_s135
for sc in stick_zsine_o6; do for s in 1 2 3; do
  out=$D/${sc}_s$s; [ -f $out/flight.ulg ] && continue
  docker ps -q --filter name=px4-indi-g5 | xargs -r docker stop >/dev/null
  timeout 600 indi_project/docker/run.sh -n g5${sc}$s -t 500 -- python3 indi_flight/bench/run_scenario.py --scenario $sc \
    --stick-mode acro --controller indi --model quad5in --seed $s --speed 4 --sim v2 --params indi_flight/results/s133_passthrough/params.params --out $out > $D/${sc}_s$s.log 2>&1
  echo "$sc s$s rc=$?" >> $D/batch_status.txt
done; done
echo DONE_ACRO >> $D/batch_status.txt
