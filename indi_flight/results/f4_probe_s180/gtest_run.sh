cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
F=src/lib/indi_rate_control/indi_rate_control.hpp
for v in 0.01f 0.03f; do
 sed -i "s/kSetpointLeadTc = [0-9.]*f/kSetpointLeadTc = $v/" $F
 echo "=== Tc $v"; ninja -C build/px4_sitl_test unit-indi_rate_control_test 2>&1 | tail -2
 ./build/px4_sitl_test/unit-indi_rate_control_test --gtest_filter="*Staircase*" 2>&1 | grep -E "staircase|FAILED|PASSED|Failure|Expected|Which is|Actual"
done
git diff --stat -- $F
make format >/dev/null 2>&1; git status --short
