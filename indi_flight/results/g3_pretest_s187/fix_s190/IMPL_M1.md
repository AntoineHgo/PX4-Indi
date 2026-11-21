# S190 M1 fix: re-seed native force filter on f_b invalid -> valid

- indi_accel_control.{hpp,cpp}: member `_prev_f_b_valid{true}` (set true in reset()). In update(), before choosing f_bf:
  edge (f_b_valid && !_prev_f_b_valid && _native_fed) -> `_lpf_f_native.reset(_last_f_b); _native_f = _last_f_b;`, then f_bf = _native_f
  as before. `_prev_f_b_valid = in.f_b_valid` each update that reaches that point. Initial true and not-fed: no edge.
- Tests (IndiAccelControlTest.cpp): ValidToInvalidSwitch bound tightened to a_f(0) in 0.5 +/- 0.05 (was < 0.6 for a 0.5 offset), |a_f(1)| < 0.05.
  New NativeRateFilterInvalidToValidHasNoStep: settle at 0.5 offset, 10 invalid cycles with no native samples, then valid with samples
  resuming: first-cycle |delta a_f| < 0.05, converges to 0.5 +/- 1e-3 after 0.5 s.
- Result: 60 tests pass (was 59), m1_test.log. astyle unchanged (m1_format.log).
- Break-check (re-seed disabled via `if (false && ...)`): new test FAILS, first-cycle step 0.5025 vs bound 0.05; 59 others pass
  (m1_breakcheck.log). Restored: 60 pass.
- px4_sitl_default rebuilt OK (m1_build.log).
