
## Review fixes (yaml wording, request timeout)
- mc_indi_rate_control_params.yaml: MC_INDI_W_MAX long text now says 0 also turns the rpm arming check off. MC_INDI_ERPM_TO
  long text now says arming is refused while the oldest sample is older than this, or while any motor has no rpm
  telemetry newer than 20 ms. The fixed 20 ms limit is IndiMeasuredTorque::SAMPLE_MAX_AGE_US, applied by compute().valid.
- McIndiRateControl.cpp updateArmingCheck(): REQUEST_TIMEOUT 3_s -> 1_s. Comment: "requests every ~300 ms, commander
  drops after ~1.2 s".
- Unit tests (`ninja -C build/px4_sitl_test test_results` in Docker, log fix_ut.log): 16/16 passed, 0 failed.
  The tests ran after the 1_s edit; the later comment-only shortening was not rebuilt.
- Format (fix_format.log): check_code_style.sh clean on all 7 C++ files, `git diff --check` clean. The first attempt
  flagged the long trailing comment, which was then shortened.
- Not committed.
