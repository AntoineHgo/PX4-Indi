#!/usr/bin/env bash
# build and run the indi_rate_control unit tests in Docker; $1 = gtest filter (default all)
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
indi_project/docker/run.sh -n s77_ut -t 2400 -- bash -c "cmake -S . -B build/px4_sitl_o11 -DCONFIG=px4_sitl_default -DCMAKE_TESTING=ON -GNinja > /dev/null; ninja -C build/px4_sitl_o11 unit-indi_rate_control_test 2>&1 | tail -n 8 && build/px4_sitl_o11/unit-indi_rate_control_test --gtest_filter='${1:-*}' 2>&1 | grep -E 'FAILED|PASSED|Failure|Which|rate error|Expected|actual|error:' | head -n 30" 2>&1 | tail -n 45
