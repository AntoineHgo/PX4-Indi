# Impl log, stage 8 task A: src/lib/indi_accel_control

- Read spec sec. 1-2, indi_rate_control CMake/header/test, control.instructions.md (applyTo does not cover src/lib/indi_*; guidelines applied anyway: PX4_ISFINITE before magnitudes).
- Created CMakeLists.txt (copy of indi_rate_control pattern), added `add_subdirectory(indi_accel_control EXCLUDE_FROM_ALL)` in src/lib/CMakeLists.txt.
- Decision: bodyzToAttitude reimplemented in the lib (quaternion only), no module target link. Tested against a hand-built expected attitude.
- Decision: min-thrust fallback uses -g_t*k_cmd*thr_min (spec says -g_t*thr_min; identical for k_cmd = 1, consistent with thrust = c/(g_t k_cmd)).
- Wrote indi_accel_control.hpp/.cpp (first draft, not yet compiled).
- Wrote IndiAccelControlTest.cpp (first draft). Next: build+test.
- First build+test: 17 pass, TiltLimit fails (investigating).
- Fixed -Wfloat-equal in lib and tests, tilt-test sign (z_b = -t_c/c, so thrust toward +x tilts z_b toward -x).
- `make tests TESTFILTER=IndiAccel` -> "100% tests passed, 0 tests failed out of 1".
- `make format` -> "Format checks passed", no file outside src/lib/indi_accel_control changed; rebuilt after format.
- unit-IndiAccelControl: "[==========] 18 tests from 1 test suite ran. (0 ms total)" / "[  PASSED  ] 18 tests."
- Behaviour notes: update() returns false before touching state for invalid p, v, q, f_b, dt (outside [1e-4, 0.5]), q norm < 0.5, mean_u if valid; NaN a_ref axis resets that axis' jerk-difference history (no spike on return); reset() must follow setFilter() (setFilter clears filter states); delay change applies at once (no slew).
