#!/usr/bin/env bash
# S163: G2 rate yaw (measured) 800/400 x2 seeds, then model-only (W_MAX 0) roll/pitch/yaw 800/400 x2 seeds. Serial.
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/g2_freeze_s160 || exit 1
CELLS="yaw:800:1 yaw:400:1 yaw:800:2 yaw:400:2" bash batch.sh || exit $?
CELLS="roll:800:1 pitch:400:1 yaw:800:1 roll:400:1 pitch:800:1 yaw:400:1 roll:800:2 roll:400:2 pitch:800:2 pitch:400:2 yaw:800:2 yaw:400:2" PSUF=_mo bash batch.sh || exit $?
echo S163_END
