#!/bin/bash
# S56: yaw M3a after D-YAW-INV option (c), bins 0.1-20 Hz, seeds 1 and 2, binary built at 23e9d30cc0.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
D=indi_flight/results/stage3_s56/yaw_m3a
indi_project/docker/run.sh -n s56build -t 3600 'make px4_sitl_default' > $D/build.log 2>&1 || { echo BUILDFAIL > $D/done.txt; exit 1; }
for s in 1 2; do n=yaw_s$s
indi_project/docker/run.sh -n s56$n -t 900 "python3 indi_flight/bench/run_scenario.py --scenario hover_long --controller indi_m3a --seed $s --speed 4 --model quad5in --params $D/yaw_lf.params --out $D/$n" > $D/${n}_stdout.log 2>&1
indi_project/docker/run.sh -n s56p$n -t 600 "bash -c 'python3 indi_flight/bench/pretest_gate.py $D/$n/flight.ulg $D/${n}_gate_preinj.md --delay 4 --length 10 > $D/${n}_gate_stdout.txt 2>&1; python3 indi_flight/bench/m3a_csv.py $D/$n/flight.ulg 2 $D/$n.csv; python3 indi_flight/bench/m3a_margins_pretest.py $D/$n.csv 0.1 20 10 > $D/${n}_margins.txt 2>&1'" > $D/${n}_post.log 2>&1
done
echo ALLDONE > $D/done.txt
