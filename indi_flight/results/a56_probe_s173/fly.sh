#!/bin/sh
# A-56 probe S173: harsh hover x3 seeds, (pos0) stock mc_pos_control + INDI rate loop, (lpf4) INDI outer loop with
# accel/thrust LPF 4 Hz instead of 10. Same command as bench/gate_g4.sh fly1 harsh hover, params file swapped.
# Run from the repo root: sh indi_flight/results/a56_probe_s173/fly.sh
set -u
O=indi_flight/results/a56_probe_s173
for cfg in pos0 lpf4; do for sd in 1 2 3; do
  n=hover_harsh_s$sd
  [ -f "$O/$cfg/$n/flight.ulg" ] && continue
  timeout 900 indi_project/docker/run.sh -n a56$cfg$sd -t 900 -- python3 indi_flight/bench/run_scenario.py \
    --controller indi --model quad5in --seed "$sd" --speed 4 --sim v2 --params $O/$cfg.params --gps-dly 110 \
    --gnss-delay 110 --scenario hover_long --vib-acc 27 --vib-gyr 0 --imu-noise-scale 4.0 --out "$O/$cfg/$n" \
    > "$O/$cfg/$n.log" 2>&1
  echo "$cfg $n rc $?" >> $O/status.txt
done; done
touch $O/FLY_DONE
