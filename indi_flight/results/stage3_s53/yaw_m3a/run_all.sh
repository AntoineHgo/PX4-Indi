#!/bin/bash
# S53 yaw M3a pre-test (INJ_AX 3, csv axis 2), seed 1, on the binary rebuilt at 7522625b0f.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
D=indi_flight/results/stage3_s53/yaw_m3a; n=yaw_s1
until grep -q ALLDONE indi_flight/results/stage3_s53/pitch_m3a/done.txt 2>/dev/null; do sleep 20; done
indi_project/docker/run.sh -n s53$n -t 900 "python3 indi_flight/bench/run_scenario.py --scenario hover_long --controller indi_m3a --seed 1 --speed 4 --model quad5in --params $D/yaw_tc050.params --out $D/$n" > $D/${n}_stdout.log 2>&1
indi_project/docker/run.sh -n s53p$n -t 600 "bash $D/post.sh $n 0.008" > $D/${n}_post.log 2>&1
echo ALLDONE > $D/done.txt
