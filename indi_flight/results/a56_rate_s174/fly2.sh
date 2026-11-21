#!/bin/sh
# A-56 rate-loop probe S174: harsh hover seed 3, freeze stack (g5_freeze_s157/params.params) with ONE inner-loop change
# per config: bld03 MC_INDI_ACT_BLD 0.3 (was 1.0), lead0 MC_INDI_LEAD 0 (was 1), dgyro15 IMU_DGYRO_CUTOFF 15 (default 30).
# Same command as results/a56_probe_s173/fly.sh. Run from the repo root: sh indi_flight/results/a56_rate_s174/fly2.sh (bld03 seeds 1-2)
set -u
O=indi_flight/results/a56_rate_s174
for cfg in bld03; do for sd in 1 2; do
  n=hover_harsh_s$sd
  [ -f "$O/$cfg/$n/flight.ulg" ] && continue
  mkdir -p $O/$cfg
  timeout 900 indi_project/docker/run.sh -n a56r$cfg -t 900 -- python3 indi_flight/bench/run_scenario.py \
    --controller indi --model quad5in --seed "$sd" --speed 4 --sim v2 --params $O/$cfg.params --gps-dly 110 \
    --gnss-delay 110 --scenario hover_long --vib-acc 27 --vib-gyr 0 --imu-noise-scale 4.0 --out "$O/$cfg/$n" \
    > "$O/$cfg/$n.log" 2>&1
  echo "$cfg $n rc $?" >> $O/status.txt
done; done
touch $O/FLY2_DONE
