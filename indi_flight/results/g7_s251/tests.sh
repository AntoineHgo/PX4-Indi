#!/usr/bin/env bash
# $1 = tag; build and run all indi unit/functional gtest targets in docker (build/px4_sitl_o11)
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
G=indi_flight/results/g7_s251
indi_project/docker/run.sh -n s251_ut -t 1700 -- bash -c "
B=build/px4_sitl_o11
cmake -S . -B \$B -DCONFIG=px4_sitl_default -DCMAKE_TESTING=ON -GNinja > /dev/null 2>&1
T=\$(ninja -C \$B -t targets all | grep -oE '^unit-[A-Za-z_]*[Ii]ndi[A-Za-z_]*|^unit-[a-z_]*indi[a-z_]*' | sort -u; echo functional-IndiMeasuredTorque)
echo targets: \$T
ok=0; n=0
for t in \$T; do n=\$((n+1)); ninja -C \$B \$t 2>&1 | grep -E 'error|FAILED' | head -20; \$B/\$t > $G/run_\$t.log 2>&1; rc=\$?; echo \$t rc=\$rc \$(grep -E '^\[  (PASSED|FAILED)' $G/run_\$t.log | tr '\n' ' '); grep -E '^\[  FAILED|Failure' -A4 $G/run_\$t.log | head -${2:-20}; [ \$rc = 0 ] && ok=\$((ok+1)); done
echo SUMMARY \$ok/\$n targets passed
" 2>&1 | tee $G/tests_$1.txt | tail -n 40
