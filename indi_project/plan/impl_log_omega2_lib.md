# Omega2 library implementation log

Task: measured actuator torque path in `src/lib/indi_rate_control/` (decision D-omega2). Library only, no module wiring, no new parameters.

## Interface added (indi_rate_control.hpp)

- `void setMeasuredTorque(const Vector3f &tau_meas, bool valid)`: for the next `update()` only. Validity is consumed (cleared) at the top of every `update()`, including rejected cycles, so a cycle without a call is invalid.
- `void setMeasurementDelaySamples(int)`: clamped to [0, kMaxDelaySamples], applied at once by `reset()`, otherwise slewed 1 sample/cycle (same logic as the model delay).
- `bool measurementInUse() const`.
- `static constexpr int kMeasValidCycles = 20`, `static constexpr float kMaxRpmRatio = 1.5f`.
- `static bool normalisedThrustFromRpm(float rpm, float rpm_max, float &u)`: spec as requested (u = (rpm/rpm_max)^2 clamped to [0,1]; false and u untouched for non finite, rpm_max <= 0, rpm < 0, rpm > 1.5 rpm_max).
- Extra logging getters (not in spec, cheap): `getFilteredModelTorque()`, `getFilteredMeasuredTorque()` (both unzeroed on ground, unlike `getFilteredTorque()`).

## Design choices

- kMeasValidCycles = 20: about 2 x (kMaxDelaySamples = 4 slew + ~6 cycles for LPF2p/alpha to settle at 1 kHz, filter taus of order 5-10 ms at 20-40 Hz cutoffs). The filters are already near the right value because they are fed `_t_act` while invalid, so this is margin for the model-vs-measurement difference and for the delay slew. At 400 Hz (test rate) it is 50 ms. The counting cycle is the first to use the measurement (the 20th consecutive valid cycle uses it).
- Invalid feed: while invalid (flag false, non finite, no call, rejected cycle) the measurement path input is the model's current `_t_act` (before the model delay), pushed through the measurement delay buffer and filters like a real sample. Consequence: the measurement path applies the measurement delay to the model value, which differs from the model path's own delay by (meas delay - model delay) samples, a small error only relevant to the bumpless switch.
- Valid measurement is constrained to [-1, 1] like the model input (overflow guard for the filters).
- Filter design sharing: `designSyncFilters()` designs the measurement filters in the same loop with the same cutoffs, same (low-passed) sample rate and same reset rules (cutoff change: settle both paths at `_t_act`; sample-rate change: LPF2p restarts at its own last output, alpha filter keeps its state). No separate design bookkeeping, so the two paths cannot diverge.
- Source selection: one counter, whole vector, no per-axis mixing. Invalid cycle: counter to 0 and fall back that same cycle.
- Rejected cycles (non finite inputs, bad dt/params): the measurement was not processed, so counter reset and `measurementInUse()` false (stricter than "states untouched"). `resetStates()` (fault-hold expiry, non finite dt_cmd) and `reset()` reset the measurement path, counter and flag. `reset()` also clears the pending measurement? No: a `setMeasuredTorque()` call before `reset()` stays pending for the next `update()` (module should call it every cycle anyway).
- Landed: measurement path runs on ground exactly like the model path; t_fb = 0 on ground whichever source is selected.
- Yaw: source selection happens before the yaw low pass and before the G2 spin-up term `(t_f - t_f_prev)`. At a switch with model != measurement, `t_f` steps and the spin-up term sees that step once (G2 > 0). Not mitigated here, left for the module/bench task (a gradual blend was rejected by the spec: no mixing).
- Model path: code and state updates unchanged; bit-identity verified by a test with all of delay, yaw cutoff and G2 active.

## Tests (12 new, suite IndiRateControlMeasurementTest) and result

All pass; the 23 existing tests are unmodified and pass.

1. NeverValidIsBitIdenticalToModelOnly (ASSERT_EQ on output and t_f, valid=false and no-call cycles, delay, yaw filter, G2)
2. MeasurementEqualToModelSwitchesWithoutTransient (external copy of the actuator model as measurement, |diff| < 1e-4 over 400 cycles of varied excitation, switch occurs)
3. SwitchesOnlyAfterRequiredValidCycles
4. OneInvalidCycleFallsBackAndRestartsCount (no-call, valid=false, rejected cycle)
5. InvalidFeedKeepsMeasurementFiltersNearModel
6. NonFiniteMeasurementIsInvalid (NaN, +inf, -inf; output finite, no fault, filters not poisoned, recovery)
7. MeasurementDelayClampsAndSlewsOneSamplePerCycle (clamp high and negative, slew bound, model path independent)
8. FollowsMeasurementWhenModelIsWrong (ACT_TC 10x off, steady state t_f and output follow measurement)
9. LandedUsesMeasurementLikeModel
10. ResetClearsMeasurementPath
11. SampleRateChangeKeepsMeasurementFiltersContinuous (weak: constant measurement)
12. NormalisedThrustFromRpm (all helper cases)

Command: `indi_project/docker/run.sh -t 1150 'make tests TESTFILTER=indi_rate_control'` -> exit 0, ctest 1/1 passed (builds in `build/px4_sitl_test`, `build/px4_sitl_default` not touched). Test binary run directly in Docker: `[  PASSED  ] 35 tests.` (23 + 12).

Format: astyle 3.1 with `Tools/astyle/astylerc` in Docker on the three files: no diff (clean). `make check_format` itself not run (whole-tree).

## Commits

- Firmware: 895b55aed8 `feat(indi): measured actuator torque path with model fallback`
- Log: see git log (`docs(indi): omega2 library implementation log`)

## Unverified / left for the module task

- No module wiring, parameters (MC_INDI_ERPM_DLY, MC_INDI_W_MAX, timeouts), tau_meas = B u computation, or per-motor validity (stale/online/plausible) logic; the helper `normalisedThrustFromRpm` is not used yet.
- kMeasValidCycles = 20 and the invalid-feed delay mismatch have not been checked on a real or SITL flight, only in gtests.
- Yaw spin-up step at the switch (see above) and the real eRPM-latency delay value are untested.
- Sample-rate redesign test for the measurement path is weak (constant input).
- Flight code size/CPU impact not measured (adds one second filter set, 5 Vector3f buffer, per cycle).
