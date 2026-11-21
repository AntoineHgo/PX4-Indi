#!/usr/bin/env bash
# G5.5 o3 s3 / o1 s1 and G4 cruise_typ_s1 with params_xyp12; stream selector $1 = a|b|c
cd "$(dirname "$0")/../../.." || exit 1
G=indi_flight/results/g55_gain_probe_s179; P=$G/params_xyp12.params
c="--controller indi --model quad5in --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0"
g55() { timeout 1000 indi_project/docker/run.sh -n s179gp_$1_s$2 -t 900 -- python3 indi_flight/bench/run_scenario.py $c --seed $2 --params $P --scenario $1 --out $G/$1_s$2 > $G/$1_s$2.stdout.log 2>&1
  python3 indi_flight/bench/g55_check.py $G/$1_s$2 --json $G/$1_s$2/g55.json > $G/$1_s$2.check.txt 2>&1; }
case $1 in
 a) g55 o3_lemniscate_gust 3;;
 b) g55 o1_lemniscate 1;;
 c) timeout 1300 indi_project/docker/run.sh -n s179gp_cruise -t 1300 -- python3 indi_flight/bench/run_scenario.py $c --seed 1 --scenario traj_lemniscate --params $P --out $G/cruise_typ_s1 > $G/cruise_typ_s1.log 2>&1;;
esac
echo done_$1 > $G/rest_$1.done
