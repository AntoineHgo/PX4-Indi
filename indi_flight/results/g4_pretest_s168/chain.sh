#!/bin/sh
# G4 pre-test (S168): one flight per profile/row, serial. Run from repo root.
P=indi_flight/results/g5_freeze_s157/params.params
O=indi_flight/results/g4_pretest_s168
fly() { name=$1; shift; timeout 900 indi_project/docker/run.sh -n s168$name -t 900 -- python3 indi_flight/bench/run_scenario.py \
  --controller indi --model quad5in --seed 1 --speed 4 --sim v2 --params $P --gps-dly 110 --gnss-delay 110 "$@" \
  --out $O/$name > $O/$name.log 2>&1; echo "$name rc $?" >> $O/status.txt; }
fly hoverL_quiet_s1 --scenario hover_long --vib-acc 0.5 --vib-gyr 0 --imu-noise-scale 1.0
fly hoverL_harsh_s1 --scenario hover_long --vib-acc 27 --vib-gyr 0 --imu-noise-scale 4.0
fly lemn_typ_s1 --scenario traj_lemniscate --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0
touch $O/CHAIN_END
