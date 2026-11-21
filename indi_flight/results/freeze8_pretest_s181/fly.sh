#!/usr/bin/env bash
# S181 freeze-8 pre-test. Repo root. Params: g5_freeze params without MC_INDI_XY_P/XY_VP (yaml default 1.2 exercised).
cd "$(dirname "$0")/../../.." || exit 1
R=indi_flight/results/freeze8_pretest_s181
c="--controller indi --model quad5in --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0"
for s in 2 3; do
 timeout 1300 indi_project/docker/run.sh -n s181_cruise_s$s -t 1300 -- python3 indi_flight/bench/run_scenario.py $c --seed $s --scenario traj_lemniscate --params $R/params_freeze.params --out $R/cruise_typ_s$s > $R/cruise_typ_s$s.log 2>&1
 echo "cruise_typ_s$s rc=$?" >> $R/done.txt
done
for sc in step_roll step_pitch step_yaw; do
 timeout 900 indi_project/docker/run.sh -n s181_$sc -t 900 -- python3 indi_flight/bench/run_scenario.py --scenario $sc --controller indi --model quad5in --sim v2 --rate-hz 800 --seed 1 --speed 4 --params indi_flight/results/g2_step_s64/indi.params --out $R/steps_seed1/${sc}_indi > $R/steps_seed1_$sc.stdout 2>&1
 echo "$sc rc=$?" >> $R/done.txt
done
echo ALLDONE >> $R/done.txt
