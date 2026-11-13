# Implementation log: indi_rate_control library

## Step 1: library files
Wrote src/lib/indi_rate_control/{CMakeLists.txt,indi_rate_control.hpp,.cpp}; added add_subdirectory(indi_rate_control) after hysteresis in src/lib/CMakeLists.txt. Not built yet.
Design notes: filters redesigned reset to current t_act (no transient); reset() keeps params, filter design and fault flag; fault flag = state of the last update(); K<0 treated as invalid parameter (fault); allocated torque input clamped to [-1,1] before the actuator model.

## Step 2: test file written
Wrote indi_rate_control_test.cpp (10 tests). Starting Docker build: make tests TESTFILTER=indi_rate_control.

## Step 3: build and test
First full "make tests" build was killed after two -Werror=float-equal errors (cutoff compare in .cpp, test compare); fixed with fabsf diff compares. Then built only the target with ninja in build/px4_sitl_test (Docker) and ran unit-indi_rate_control_test: 10/10 PASSED, no thresholds changed. Not run: ASAN/UBSAN variant (make tests sets sanitizer env), full make tests path.
