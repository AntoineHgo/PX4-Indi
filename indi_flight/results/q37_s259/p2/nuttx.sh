cd /tmp/indi_fwbranch_s251
O=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/q37_s259
for t in indi default; do s=$(date +%s); make px4_fmu-v5x_$t > $O/build_nuttx_v5x_$t.log 2>&1; echo "rc=$? $(( $(date +%s)-s )) s" >> $O/build_nuttx_v5x_$t.log; done
arm-none-eabi-size build/px4_fmu-v5x_indi/px4_fmu-v5x_indi.elf build/px4_fmu-v5x_default/px4_fmu-v5x_default.elf > $O/size.txt 2>&1
