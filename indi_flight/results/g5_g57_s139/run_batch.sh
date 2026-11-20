#!/usr/bin/env bash
# S139 G5.7 mode_switch10 and G5.3-hold hold_wind probes (GATES 5b), seeds $SEEDS (default 1 2 3), scenarios $SCS. Serial, from anywhere.
# Skips runs whose flight.ulg exists. Output <scenario>_s<seed>; checkers at the end (summary g57_summary.txt, g53_hold_summary.txt).
cd "$(dirname "$0")/../../.."
D=indi_flight/results/g5_g57_s139
for s in ${SEEDS:-1 2 3}; do for sc in ${SCS:-mode_switch10 hold_wind}; do
  out=$D/${sc}_s$s; [ -f $out/flight.ulg ] && continue
  ov=""; [ $sc = hold_wind ] && ov="--scenario-overrides $D/hold_wind_overrides.json"
  docker ps -q --filter name=px4-indi-g5g57 | xargs -r docker stop >/dev/null
  timeout 600 indi_project/docker/run.sh -n g5g57${sc//_/}$s -t 500 -- python3 indi_flight/bench/run_scenario.py --scenario $sc \
    --stick-mode posctl --controller indi --model quad5in --seed $s --speed 4 --sim v2 --params $D/params.params $ov --out $out > $D/${sc}_s$s.log 2>&1
  echo "$sc s$s rc=$?" >> $D/batch_status.txt
done; done
echo DONE >> $D/batch_status.txt
python3 indi_flight/bench/g57_check.py $D/mode_switch10_s? 2>&1 | tee $D/g57_summary.txt
python3 indi_flight/bench/g53_hold_check.py $D/hold_wind_s? 2>&1 | tee $D/g53_hold_summary.txt
