cd /tmp/indi_fwbranch_s251
L=/tmp/indi_fwbranch_s251/s251_tests_func.log
T=$(ninja -C build/px4_sitl_test -t targets all | grep -oE '^functional-[A-Za-z_]*([Ii]ndi|Torque)[A-Za-z_]*' | sort -u)
echo "targets: $T" > $L
for t in $T; do ninja -C build/px4_sitl_test $t >> $L 2>&1; echo "build $t rc=$?" >> $L; ./build/px4_sitl_test/$t 2>&1 | tail -4 >> $L; echo "run $t rc=${PIPESTATUS[0]}" >> $L; done
