#!/bin/bash
# S56: yaw M3a after D-YAW-INV option (c), bins 5-40 Hz, seeds 1 and 2, binary rebuilt at HEAD.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
D=indi_flight/results/stage3_s57_pre/yaw_m3a_hf
indi_project/docker/run.sh -n s56hbuild -t 3600 'make px4_sitl_default' > $D/build.log 2>&1 || { echo BUILDFAIL > $D/done.txt; exit 1; }
for s in 1 2; do n=yaw_s$s
indi_project/docker/run.sh -n s56h$n -t 900 "python3 indi_flight/bench/run_scenario.py --scenario hover_long --controller indi_m3a --seed $s --speed 4 --model quad5in --params $D/yaw_hf.params --out $D/$n" > $D/${n}_stdout.log 2>&1
indi_project/docker/run.sh -n s56hp$n -t 600 "bash -c 'python3 indi_flight/bench/pretest_gate.py $D/$n/flight.ulg $D/${n}_gate_preinj.md --delay 4 --length 10 > $D/${n}_gate_stdout.txt 2>&1; python3 indi_flight/bench/m3a_csv.py $D/$n/flight.ulg 2 $D/$n.csv; python3 indi_flight/bench/m3a_margins_pretest.py $D/$n.csv 5 40 10 > $D/${n}_margins.txt 2>&1'" > $D/${n}_post.log 2>&1
done
echo ALLDONE > $D/done.txt
