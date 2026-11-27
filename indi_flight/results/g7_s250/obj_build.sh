#!/usr/bin/env bash
# $1 = tag (before|after): build McIndiRateControl.cpp.o in docker and keep its disassembly
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
G=indi_flight/results/g7_s250
indi_project/docker/run.sh -n s250_obj -t 1700 -- bash -c "
cmake -S . -B build/px4_sitl_o11 -DCONFIG=px4_sitl_default -DCMAKE_TESTING=ON -GNinja > $G/obj_cmake_$1.log 2>&1
O=\$(ninja -C build/px4_sitl_o11 -t targets all | grep -oE '^[^ :]*mc_indi_rate_control\.dir/McIndiRateControl\.cpp\.o' | head -1)
echo target \$O
ninja -C build/px4_sitl_o11 \$O 2>&1 | tail -n 3
cp build/px4_sitl_o11/\$O $G/obj/McIndiRateControl_$1.o
objdump -dr --no-show-raw-insn $G/obj/McIndiRateControl_$1.o > $G/obj/McIndiRateControl_$1.dis
"
