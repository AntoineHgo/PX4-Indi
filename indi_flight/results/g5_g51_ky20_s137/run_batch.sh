#!/usr/bin/env bash
# S137 G5.1 acro probe at MC_INDI_K_Y 20: stick_steps, --stick-mode acro and stabilized, seeds 1-3 (GATES 5b). Serial, from anywhere.
# Skips runs whose flight.ulg exists (resume = rerun this script). Output: <mode-short>_s<seed>; then python3 indi_flight/bench/g51_check.py on each.
cd "$(dirname "$0")/../../.."
D=indi_flight/results/g5_g51_ky20_s137
for s in ${SEEDS:-1 2 3}; do for m in ${MODES:-acro:acro stabilized:stab}; do
  mode=${m%%:*}; short=${m##*:}
  out=$D/${short}_s$s; [ -f $out/flight.ulg ] && continue
  docker ps -q --filter name=px4-indi-g5 | xargs -r docker stop >/dev/null
  timeout 600 indi_project/docker/run.sh -n g5ky20${short}$s -t 500 -- python3 indi_flight/bench/run_scenario.py --scenario stick_steps \
    --stick-mode $mode --controller indi --model quad5in --seed $s --speed 4 --sim v2 --stick-pilot --params $D/params.params --out $out > $D/${short}_s$s.log 2>&1
  echo "$short s$s rc=$?" >> $D/batch_status.txt
done; done
echo DONE >> $D/batch_status.txt
python3 indi_flight/bench/g51_check.py $D/acro_s? $D/stab_s? 2>&1 | tee $D/g51_summary.txt
