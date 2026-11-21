#!/bin/bash
# PID reference flights for the Q19 skipped-window guard (S183). Stock PID (--controller pid, no params file), same plant/profile flags
# as gate_g4.sh and a56_pid_s173/fly.sh. Serial; a run with flight.ulg is skipped; one retry per run.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi || exit 1
O=indi_flight/results/freeze9_s183/g4_pid
for r in hover_harsh_s1 hover_harsh_s2 cruise_harsh_s1 cruise_harsh_s2; do
  fl=${r%%_*}; sd=${r##*_s}; sc=traj_lemniscate; [ $fl = hover ] && sc=hover_long
  for try in 1 2; do
    [ -f $O/$r/flight.ulg ] && break
    timeout 900 indi_project/docker/run.sh -n g4f9pid_$r -t 900 -- python3 indi_flight/bench/run_scenario.py \
      --controller pid --model quad5in --seed $sd --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 \
      --scenario $sc --vib-acc 27 --vib-gyr 0 --imu-noise-scale 4.0 --out $O/$r > $O/$r.log 2>&1
    echo "$r try$try rc $?" >> $O/status.txt
  done
done
touch $O/FLY_DONE
