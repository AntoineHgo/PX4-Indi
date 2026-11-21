#!/bin/sh
# A-56 PID reference (S173): stock PID, harsh hover seeds 2-3 (seed 1 = results/a54_s169/pid_hover_harsh_s1), same
# flags as that run (stock params, no params file). Question: does PID also show the s3 2 Hz line? Waits for the
# G3 pre-test (results/g3_pretest_s173/FLY_DONE) so runs stay serial. Run from the repo root.
set -u
O=indi_flight/results/a56_pid_s173
while [ ! -f indi_flight/results/g3_pretest_s173/FLY_DONE ]; do sleep 30; done
for sd in 2 3; do
  n=pid_hover_harsh_s$sd
  [ -f "$O/$n/flight.ulg" ] && continue
  timeout 900 indi_project/docker/run.sh -n a56pid$sd -t 900 -- python3 indi_flight/bench/run_scenario.py \
    --controller pid --model quad5in --seed "$sd" --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 \
    --scenario hover_long --vib-acc 27 --vib-gyr 0 --imu-noise-scale 4.0 --out "$O/$n" > "$O/$n.log" 2>&1
  echo "$n rc $?" >> $O/status.txt
done
touch $O/FLY_DONE
