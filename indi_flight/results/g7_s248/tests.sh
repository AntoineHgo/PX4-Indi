cd /tmp/indi_fwbranch_s248
L=/tmp/indi_fwbranch_s248/s248_tests.log
cmake -S . -B build/px4_sitl_test -GNinja -DCONFIG=px4_sitl_test > $L 2>&1; echo cfg rc=$? >> $L
T=$(ninja -C build/px4_sitl_test -t targets all | grep -oE '^unit-[A-Za-z_]*[Ii]ndi[A-Za-z_]*|^unit-[a-z_]*indi[a-z_]*' | sort -u)
echo "targets: $T" >> $L
for t in $T; do ninja -C build/px4_sitl_test $t >> $L 2>&1; echo "build $t rc=$?" >> $L; ./build/px4_sitl_test/$t 2>&1 | tail -4 >> $L; echo "run $t rc=${PIPESTATUS[0]}" >> $L; done
