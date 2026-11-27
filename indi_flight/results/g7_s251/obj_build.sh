#!/usr/bin/env bash
# $1 = tag (before|after): build McIndiPosControl.cpp.o and McIndiRateControl.cpp.o in docker, keep disassembly
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
G=indi_flight/results/g7_s251
indi_project/docker/run.sh -n s251_obj -t 1700 -- bash -c "
cmake -S . -B build/px4_sitl_o11 -DCONFIG=px4_sitl_default -DCMAKE_TESTING=ON -GNinja > $G/obj_cmake_$1.log 2>&1
for M in McIndiPosControl:mc_indi_pos_control McIndiRateControl:mc_indi_rate_control; do
F=\${M%%:*}; D=\${M##*:}
O=\$(ninja -C build/px4_sitl_o11 -t targets all | grep -oE \"^[^ :]*\$D\.dir/\$F\.cpp\.o\" | head -1)
echo target \$O
ninja -C build/px4_sitl_o11 \$O 2>&1 | tail -n 3
cp build/px4_sitl_o11/\$O $G/obj/\${F}_$1.o
objdump -dr --no-show-raw-insn $G/obj/\${F}_$1.o > $G/obj/\${F}_$1.dis
done
"
