#!/bin/bash
# two parallel streams
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/stage3_s53/act_tc_sweep
(bash fly.sh 0.066 1; bash fly.sh 0.050 1) &
(bash fly.sh 0.066 2; bash fly.sh 0.0165 1) &
wait; echo ALLDONE >> done.txt
