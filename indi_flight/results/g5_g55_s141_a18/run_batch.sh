#!/usr/bin/env bash
# S141 G5.5 probe with A18 jerk feed-forward on (otherwise identical to g5_g55_s140_gnss: matched GNSS 110 ms).
# usage: run_batch.sh "scenario ..." "seeds ..."; skips runs whose flight.ulg exists; stops only px4-indi-x56* containers.
cd "$(dirname "$0")/../../.."
D=indi_flight/results/g5_g55_s141_a18
SC=${1:-"o1_lemniscate o2_circle_z"}; SD=${2:-"1"}
for sc in $SC; do for s in $SD; do
  out=$D/${sc}_s$s; [ -f $out/flight.ulg ] && continue
  docker ps -q --filter name=px4-indi-x56 | xargs -r docker stop >/dev/null
  timeout 700 indi_project/docker/run.sh -n x56${sc%%_*}$s -t 600 -- python3 indi_flight/bench/run_scenario.py --scenario $sc \
    --controller indi --model quad5in --seed $s --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 --params $D/params.params --out $out > $D/${sc}_s$s.log 2>&1
  echo "$sc s$s rc=$?" >> $D/batch_status.txt
  python3 indi_flight/bench/g55_check.py $out --json $out.json > /dev/null 2>&1
done; done
echo DONE >> $D/batch_status.txt
