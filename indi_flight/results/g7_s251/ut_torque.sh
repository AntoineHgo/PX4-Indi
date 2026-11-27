#!/usr/bin/env bash
# build and run the functional-IndiMeasuredTorque target in docker (build/px4_sitl_o11)
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
G=indi_flight/results/g7_s251
indi_project/docker/run.sh -n s251_torque -t 1500 -- bash -c "
B=build/px4_sitl_o11
cmake -S . -B \$B -DCONFIG=px4_sitl_default -DCMAKE_TESTING=ON -GNinja > /dev/null 2>&1
ninja -C \$B functional-IndiMeasuredTorque 2>&1 | grep -E 'error|warning|FAILED' | head -20
\$B/functional-IndiMeasuredTorque 2>&1 | tee $G/run_torque_$1.log | grep -E '^\[  (PASSED|FAILED)|Failure|Expected|Which is|actual|\[ RUN' | grep -v RUN | head -30
" 2>&1 | tail -n 40
