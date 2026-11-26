cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
L=indi_flight/results/g7_s249/p3c_tests2.log
: > $L
for t in unit-EkfResetDetect unit-FailsafeSetpoint unit-SetpointExtrapolation functional-IndiMeasuredTorque; do ninja -C build/px4_sitl_test $t >> $L 2>&1; echo "build $t rc=$?" >> $L; ./build/px4_sitl_test/$t 2>&1 | tail -3 >> $L; echo "run $t rc=${PIPESTATUS[0]}" >> $L; done
