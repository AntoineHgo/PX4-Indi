INDI unit tests, HEAD 353c017971 (clean tree), all three pass.

Commands (Docker, px4-indi-sim image):
  indi_project/docker/run.sh -n tgt -t 1200 'cd build/px4_sitl_test && ninja unit-indi_rate_control_test unit-IndiAccelControl functional-IndiMeasuredTorque'
  then ./unit-indi_rate_control_test, ./unit-IndiAccelControl, ./functional-IndiMeasuredTorque (in build/px4_sitl_test)

Results:
- unit-indi_rate_control_test: [  PASSED  ] 40 tests.  (40 run, 0 failed)
- unit-IndiAccelControl: [  PASSED  ] 19 tests.  (19 run, 0 failed)
- functional-IndiMeasuredTorque: [  PASSED  ] 4 tests.  (4 run, 0 failed)

Build: ninja ran in build/px4_sitl_test against the current tree; the binaries were relinked during this run, so they reflect the current HEAD sources. Ninja's up-to-date check is mtime-based.
Target names came from ninja -t targets (not ctest; the px4 test names differ from the source file names).
