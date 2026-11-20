#!/usr/bin/env bash
# S139 G5.5 batch: o1..o7 + offb_vel_step, seeds 1-3, serial, INDI stack, params = g5_g52_s138 (MC_RATE_CTL_TYPE 1, MC_INDI_POS_EN 1).
# usage: run_batch.sh "scenario ..." "seeds ..."   (default: all, 1 2 3). Skips runs whose flight.ulg exists. Stops only containers named px4-indi-x55*.
cd "$(dirname "$0")/../../.."
D=indi_flight/results/g5_g55_s139
SC=${1:-"o1_lemniscate o2_circle_z o3_lemniscate_gust o4_lemniscate_payload o5_zsine_com_shift o6_zsine_mass o7_lemniscate_tau2 offb_vel_step"}
SD=${2:-"1 2 3"}
for sc in $SC; do for s in $SD; do
  out=$D/${sc}_s$s; [ -f $out/flight.ulg ] && continue
  docker ps -q --filter name=px4-indi-x55 | xargs -r docker stop >/dev/null
  timeout 700 indi_project/docker/run.sh -n x55${sc%%_*}$s -t 600 -- python3 indi_flight/bench/run_scenario.py --scenario $sc \
    --controller indi --model quad5in --seed $s --speed 4 --sim v2 --params $D/params.params --out $out > $D/${sc}_s$s.log 2>&1
  echo "$sc s$s rc=$?" >> $D/batch_status.txt
done; done
echo DONE >> $D/batch_status.txt
