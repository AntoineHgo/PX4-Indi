#!/usr/bin/env bash
# S138 G5.2 probe: stick_pos_steps, --stick-mode altctl and posctl, seeds 1-3 (GATES 5b). Serial, from anywhere.
# Skips runs whose flight.ulg exists (resume = rerun). Output: <mode>_s<seed>; then python3 indi_flight/bench/g52_check.py on each.
cd "$(dirname "$0")/../../.."
D=indi_flight/results/g5_g52_s138
for s in ${SEEDS:-1 2 3}; do for mode in ${MODES:-altctl posctl}; do
  out=$D/${mode}_s$s; [ -f $out/flight.ulg ] && continue
  docker ps -q --filter name=px4-indi-g5 | xargs -r docker stop >/dev/null
  timeout 600 indi_project/docker/run.sh -n g5g52${mode}$s -t 500 -- python3 indi_flight/bench/run_scenario.py --scenario stick_pos_steps \
    --stick-mode $mode --controller indi --model quad5in --seed $s --speed 4 --sim v2 --params $D/params.params --out $out > $D/${mode}_s$s.log 2>&1
  echo "$mode s$s rc=$?" >> $D/batch_status.txt
done; done
echo DONE >> $D/batch_status.txt
python3 indi_flight/bench/g52_check.py $D/altctl_s? $D/posctl_s? 2>&1 | tee $D/g52_summary.txt
