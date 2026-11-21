#!/usr/bin/env bash
# Pre-test (roll 800 s1, yaw 800 s1) then, only if both have margins and attitude_break_check RESULT PASS, the 10 other cells.
set -u
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi || exit 1
G=indi_flight/results/g2_att_freeze_s162
CELLS="1:800:1 3:800:1" bash $G/batch.sh || { echo "PRETEST_ABORT"; exit 12; }
for n in ax1_r800_s1 ax3_r800_s1; do grep -q 'RESULT PASS' $G/${n}_check.txt || { echo "PRETEST_CHECK_FAIL $n"; exit 13; }; done
echo PRETEST_OK
CELLS="2:800:1 1:400:1 2:400:1 3:400:1 1:800:2 2:800:2 3:800:2 1:400:2 2:400:2 3:400:2" bash $G/batch.sh
echo CHAIN_END
