cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
L=indi_flight/results/g7_s249/p3c_tests.log
: > $L
ninja -C build/px4_sitl_test -t targets all > /tmp/p3c_targets.txt 2>/dev/null
T=$(grep -oE '^unit-[A-Za-z_]*[Ii]ndi[A-Za-z_]*' /tmp/p3c_targets.txt | sort -u)
echo "targets: $T" >> $L
for t in $T; do ninja -C build/px4_sitl_test $t >> $L 2>&1; echo "build $t rc=$?" >> $L; ./build/px4_sitl_test/$t 2>&1 | tail -3 >> $L; echo "run $t rc=${PIPESTATUS[0]}" >> $L; done
echo DONE >> $L
