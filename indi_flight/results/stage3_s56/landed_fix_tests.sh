#!/bin/bash
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
D=indi_flight/results/stage3_s56; F=src/lib/indi_rate_control/indi_rate_control.cpp
indi_project/docker/run.sh -n s56t1 -t 2400 'make tests TESTFILTER=indi_rate_control' > $D/landed_fix_tests_green.txt 2>&1; echo "green rc=$?" > $D/landed_fix_tests_rc.txt
sed -i 's/(i == 2 \&\& !landed) ? _yaw_inc_prev/(i == 2) ? _yaw_inc_prev/' $F
indi_project/docker/run.sh -n s56t2 -t 2400 'make tests TESTFILTER=indi_rate_control' > $D/landed_fix_tests_broken.txt 2>&1; echo "broken rc=$?" >> $D/landed_fix_tests_rc.txt
sed -i 's/(i == 2) ? _yaw_inc_prev/(i == 2 \&\& !landed) ? _yaw_inc_prev/' $F
grep -c '!landed) ? _yaw_inc_prev' $F >> $D/landed_fix_tests_rc.txt
echo DONE >> $D/landed_fix_tests_rc.txt
